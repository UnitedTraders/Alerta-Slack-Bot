import logging
from flask import Flask
from flask import request
from flask import make_response

import os
import json
import sys
import urllib
import requests

from slack.web.client import WebClient
from slack.web.classes import dialogs


app = Flask(__name__)

app.config.from_pyfile('../alerta_bot.conf', silent=True)

logging.basicConfig(level=logging.INFO)

SLACK_API_KEY = app.config.get('SLACK_API_KEY', '')
BOT_ENDPOINT_KEY = app.config.get('BOT_ENDPOINT_KEY', '')
BOT_PORT = app.config.get('BOT_PORT', '8666')
ALERTA_API_ROOT = app.config.get('ALERTA_API_ROOT', '')
ALERTA_API_KEY = app.config.get('ALERTA_API_KEY', '')

slack_client = WebClient(SLACK_API_KEY, timeout=30)


def make_alerta_action(ALERT_ID, ALERT_ACTION, ALERT_ACTION_TIME, COMMENT):

    headers = {'Authorization': f'Key {ALERTA_API_KEY}'}

    if ALERT_ACTION == "note":
        ALERTA_API_URL = f'{ALERTA_API_ROOT}/alert/{ALERT_ID}/note'
        alerta_action = {
            "note": COMMENT
        }
    else:
        ALERTA_API_URL = f'{ALERTA_API_ROOT}/alert/{ALERT_ID}/action'
        alerta_action = {
            "action": ALERT_ACTION,
            "timeout": ALERT_ACTION_TIME,
            "text": COMMENT
        }

    requests.put(ALERTA_API_URL, json=alerta_action, headers=headers)


def return_response_to_slack(SLACK_RESPONSE_URL, SLACK_USER, ALERT_TEXT, ALERT_ACTION, ALERT_ACTION_TIME, COMMENT):

    time_values = {"300": "5 mins", "900": "15 mins", "1800": "30 mins", "3600": "1 hour", "7200": "2 hours", "14400": "4 hours", "28800": "8 hours",
                   "86400": "1 day", "604800": "1 week"}
    response_body = {
        "text": f"Thank you for the response, {SLACK_USER}",
        "attachments": [
            {
                "text": ALERT_TEXT
            },
            {
                "text": f"{COMMENT} ({time_values[ALERT_ACTION_TIME]})"
            },
            {
                "text": "Waka-waka :space_invader:"
            }
        ],
        "response_type": "in_channel"
    }

    requests.post(SLACK_RESPONSE_URL, json=response_body)


def make_dialog_for_ack(SLACK_TRIGGER_ID, ALERT_ID, SLACK_USER, ALERT_TEXT):

    ack_options = [
        {
            "label": "Ack for 5 mins",
            "value": "ack|300"
        },
        {
            "label": "Ack for 15 mins",
            "value": "ack|900"
        },
        {
            "label": "Ack for 30 mins",
            "value": "ack|1800"
        },
        {
            "label": "Ack for 1 hour",
            "value": "ack|3600"
        },
        {
            "label": "Ack for 2 hours",
            "value": "ack|7200"
        },
        {
            "label": "Ack for 4 hours",
            "value": "ack|14400"
        },
        {
            "label": "Ack for 8 hours",
            "value": "ack|28800"
        },
        {
            "label": "Ack for 1 day",
            "value": "ack|86400"
        },
        {
            "label": "Ack for 1 week",
            "value": "ack|604800"
        },
        {
            "label": "Close alert",
            "value": "close|604800"
        }
    ]

    builder = (
        dialogs.DialogBuilder()
        .title("Ack or close the alert")
        .state({'alert_id': ALERT_ID, 'type': 'ack', 'alert_text': ALERT_TEXT})
        .callback_id(f"{ALERT_ID}|ack")
        .static_selector(name="action", label="What to do?", placeholder="Choose an option", options=ack_options)
        .text_area(name="note", label="Note", hint="Write comment to the acked alert", max_length=500)
    )

    slack_client.dialog_open(dialog=builder.to_dict(),
                             trigger_id=SLACK_TRIGGER_ID)

    return make_response("", 200)


def make_dialog_for_comment(SLACK_TRIGGER_ID, ALERT_ID, SLACK_USER, ALERT_TEXT):

    builder = (
        dialogs.DialogBuilder()
        .title("Add a note to the alert")
        .state({'alert_id': ALERT_ID, 'type': 'comment', 'alert_text': ALERT_TEXT})
        .callback_id(f"{ALERT_ID}|comment")
        .text_area(name="note", label="Note", hint="Write something useful", max_length=500)
    )

    slack_client.dialog_open(dialog=builder.to_dict(),
                             trigger_id=SLACK_TRIGGER_ID)

    return make_response("", 200)

@app.route('/')
def main_page():
    return make_response("", 201)


@app.route(f'/{BOT_ENDPOINT_KEY}/webhook', methods=['GET', 'POST'])
def manage_alerta():

    slack_payload = json.loads(request.form.get('payload'))

    # print(json.dumps(slack_payload))

    #parse slack payload
    BOT_ACTION = slack_payload["type"]

    # clicking on buttons
    if BOT_ACTION == 'block_actions':

        SLACK_USER = slack_payload["user"]["username"]
        SLACK_TRIGGER_ID = slack_payload["trigger_id"]
        ALERT_TEXT = slack_payload["message"]["blocks"][0]["text"]["text"]
        ALERT_ID = slack_payload["message"]["blocks"][1]["elements"][0]["text"]

        if slack_payload["actions"][0]["value"] == "ack_alert":
            make_dialog_for_ack(SLACK_TRIGGER_ID, ALERT_ID,
                                SLACK_USER, ALERT_TEXT)

        elif slack_payload["actions"][0]["value"] == "comment_alert":
            make_dialog_for_comment(
                SLACK_TRIGGER_ID, ALERT_ID, SLACK_USER, ALERT_TEXT)

    # submitting a dialog
    elif BOT_ACTION == 'dialog_submission':
        SLACK_RESPONSE_URL = slack_payload["response_url"]
        ACTION_STATE = json.loads(slack_payload["state"])
        SLACK_USER = slack_payload["user"]["name"]
        COMMENT = slack_payload["submission"]["note"]

        if ACTION_STATE["type"] == "ack":
            ALERT_ACTION, ALERT_ACTION_TIME = slack_payload["submission"]["action"].split("|")
            make_alerta_action(ACTION_STATE["alert_id"], ALERT_ACTION, ALERT_ACTION_TIME, COMMENT)
            return_response_to_slack(
                SLACK_RESPONSE_URL, SLACK_USER, ACTION_STATE["alert_text"], ALERT_ACTION, ALERT_ACTION_TIME, COMMENT)

        elif ACTION_STATE["type"] == "comment":
            make_alerta_action(ACTION_STATE["alert_id"], "note", 0, COMMENT)

    return make_response("", 200)


if __name__ == '__main__':
    port = int(BOT_PORT)
    app.run(port=port, host='0.0.0.0')
