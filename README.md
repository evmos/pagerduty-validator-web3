# Pagerduty for web3 chains

Simple API to send notifications to your pager duty API if you are missing blocks

## Requirements

- python3 (`sudo apt-get install python3 python3-dev python3-venv`)
- Pagerduty API key
- Validator address (`ethmvaloper1...`)

## Set up your key

In your Pagerduty service add the integration with `Events API V2` and save your integration key

## Usage

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
router_key=PUT_YOUR_KEY_HERE val_key="ethmvaloper1..." python3 main.py
```

## Alerts

- It will alert you if the APIs do not return a new height after 2 minutes
- It will alert you if you have missed more than 2k blocks out of the last 90k (Slashing starts at 45k blocks missed)
- It will limit the alerts to 1 every 5minutes

## Logs

By default the logger is in DEBUG mode, it can be set to INFO to avoid getting spammed with the API requests logs.
