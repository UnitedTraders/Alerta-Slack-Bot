# Slack bot for Alerta

This is simple Slack bot. It's able to ack and comment Alerta events, which sent to Slack via [alerta_slack](https://github.com/alerta/alerta-contrib/blob/master/plugins/slack/alerta_slack.py) plugin.

## Build and run

* Docker build: `docker build -t alerta-slack-bot:latest .`
* Docker run: `docker run -p 8666:8666 -v $(pwd)/alerta_bot.conf:/app/alerta_bot.conf alerta-slack-bot:latest`

## Configuration

```python
# OAuth Access Token for slack application
SLACK_API_KEY = 'xoxp-YOUR-SLACK-BOT-API-KEY'

# some kind of security - requests will be sent to /LONG_RANDOM_STRING/webhook instead of /webhook
BOT_ENDPOINT_KEY = 'LONG_RANDOM_STRING'

# port to bind
BOT_PORT = '8666'

# URL of Alerta API endpoint
ALERTA_API_ROOT = 'https://alerts.example.com/api'

# key for alerta user (need read and wrie scopes)
ALERTA_API_KEY = "API-KEY-FOR-ALERTA-USER"
```

## Sample payload for Slack

From `alertad.conf`:

```python
SLACK_PAYLOAD = {
  "channel": "{{ channel }}",
  "emoji": ":bear-sat:",
  "icon_emoji": ":bear-sat:",
  "blocks": "[{\"type\": \"section\",\"block_id\": \"header\",\"text\": {\"type\": \"mrkdwn\",\"text\": \"*[{{ alert.environment }}]* :: _{{ status }}_ :: _{{ alert.severity|capitalize }}_ :: _{{ alert.value }}_\n```{{ alert.text }}```\"}},{\"type\": \"context\",\"block_id\": \"alert_id\",\"elements\": [{\"type\": \"mrkdwn\",\"text\": \"{{ alert.id }}\"}]}]",
  "attachments": "[{\"color\":\"{{color}}\", \"blocks\": [{\"type\": \"section\",\"block_id\": \"labels\",\"fields\": [{\"type\": \"mrkdwn\",\"text\": \"*Resource:* {{ alert.resource }}\"},{\"type\": \"mrkdwn\",\"text\": \"*Services:* {{ alert.service|join(', ') }}\"},{\"type\": \"mrkdwn\",\"text\": \"*Event:* {{ alert.event }}\"},{\"type\": \"mrkdwn\",\"text\": \"*Origin:* {{ alert.origin }}\"},{\"type\": \"mrkdwn\",\"text\": \"*<{{ config.DASHBOARD_URL }}/#/alert/{{ alert.id }}|Alert Console>*\"}]},{% if status != 'closed' %}{\"type\": \"actions\",\"elements\": [{\"type\": \"button\",\"text\": {\"type\": \"plain_text\",\"text\": \"Ack me :white_check_mark:\",\"emoji\": true},\"value\": \"ack_alert\"},{\"type\": \"button\",\"text\": {\"type\": \"plain_text\",\"text\": \"Comment me :memo:\",\"emoji\": true},\"value\": \"comment_alert\"}]}{% else %}{\"type\": \"actions\",\"elements\": [{\"type\": \"button\",\"text\": {\"type\": \"plain_text\",\"text\": \"Comment me :memo:\",\"emoji\": true},{% endif %} ]}]"
}
```

## TODO

* Use WSGI server instead of Flask dev server
* Make messages configurable
