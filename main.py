import logging
import os
import signal
import time

import requests


# Logger
logger = logging.getLogger()
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('[%(asctime)s][%(levelname)s]: %(message)s', '%H:%M:%S'))
logger.setLevel(logging.DEBUG)
logger.addHandler(handler)

# Env Var
val_key = os.getenv("val_key","ethmvaloper1kdtjxywfvwq94jsst2uyshwkel6dwdv5vlf4l2")
routing_key = os.getenv('routing_key')
if routing_key is None:
    logger.error('The routing key is missing!')
    raise (SystemExit(1))


# Set up globals
ALLOWED_OFFSET = int(10)
LAST_ALERT = None
CURRENT_NETWORK_BLOCK = None
LAST_UPDATE = time.time()
RUNNING = True

MAX_TIMEOUT = 120

# Api
url = 'https://rpc-evm-sidechain.xrpl.org'

def get_height(url):
    try:
        queryData = '{"jsonrpc":"2.0","method":"eth_getBlockByNumber","params":["latest", false],"id":1}'
        res = requests.post(url, data=queryData, headers={"Content-type": "application/json"}).json()
        logger.debug(f'Getting height from {url}')
        return int(res['result']['number'],16)
    except Exception as e:
        print(e)
        return None


def get_status():
    global CURRENT_NETWORK_BLOCK
    global LAST_UPDATE

    CURRENT_NETWORK_BLOCK = get_height(url)

    if CURRENT_NETWORK_BLOCK is None:
        # RPC down
        if time.time() - LAST_UPDATE > MAX_TIMEOUT:
            logger.info('Sending alert: No valid response')
            send_alert(text=f'No valid response after {MAX_TIMEOUT} seconds')

        return False


    LAST_UPDATE = time.time()



    our_node_heigth = get_height("http://localhost:8545")
    if our_node_heigth is None:
        logger.info('Sending alert: No valid response from our node')
        send_alert(text=f'No valid response from our node')
        return False

    if CURRENT_NETWORK_BLOCK + ALLOWED_OFFSET < our_node_heigth:
        # The height is lower than our last stored height (endpoints are not in sync)
        logger.debug('The height is lower than our last stored height (endpoints are not in sync)')
        return False


    LAST_UPDATE = time.time()

    if our_node_heigth < CURRENT_NETWORK_BLOCK - ALLOWED_OFFSET:
        logger.info(f'Sending alert: Node is not up to date')
        send_alert(blocks_missed=str(CURRENT_NETWORK_BLOCK - our_node_heigth))
        return False

    return True


# Pager duty
def generate_body(blocks_missed='?', text='Missing blocks!'):
    return {
        'payload': {
            'summary': text,
            'severity': 'critical',
            'source': 'EVM Validator',
            'component': 'validator',
            'custom_details': {
                'blocks missed': str(blocks_missed),
            }
        },
        'routing_key':
        str(routing_key),
        'event_action':
        'trigger',
        'client':
        'Validator Monitoring Service',
        'client_url':
        'https://evmos.org',
        'links': [{
            'href': 'https://validators.evm-sidechain.xrpl.org/xrp/validators/ethmvaloper1kdtjxywfvwq94jsst2uyshwkel6dwdv5vlf4l2',
            'text': 'Explorer link!'
        }],
        'images': [{
            'src': 'https://images.pexels.com/photos/1805164/pexels-photo-1805164.jpeg',
            'href': 'https://google.com',
            'alt': 'There is no need for this'
        }]
    }


def send_alert(blocks_missed='?', text='Missing blocks!'):
    global LAST_ALERT

    if LAST_ALERT is not None:
        if time.time() - LAST_ALERT < 5 * 60:
            # Only send 1 alert every 5min
            return False

    x = requests.post('https://events.eu.pagerduty.com/v2/enqueue',
                      json=generate_body(blocks_missed=blocks_missed, text=text))
    while x.status_code != 202:
        logger.error(f'Waiting 1 min to resend the alert, status code: {x.status_code}')
        time.sleep(60 * 1)
        x = requests.post('https://events.eu.pagerduty.com/v2/enqueue',
                          json=generate_body(blocks_missed=blocks_missed, text=text))

    logger.info('Alert sent!')
    LAST_ALERT = time.time()
    return True


# Handel control + c
def kill_handler(signum, frame):
    global RUNNING
    _ = signum
    _ = frame
    logger.info('Closing the program...')
    RUNNING = False


if __name__ == '__main__':
    signal.signal(signal.SIGINT, kill_handler)
    while RUNNING:
        get_status()
        # Wait at least 2 seconds for the next block
        time.sleep(2)

    raise (SystemExit(0))
