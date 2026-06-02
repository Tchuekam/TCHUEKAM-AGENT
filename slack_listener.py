"""
TCHUEKAM Slack Socket Mode Listener
Runs as a standalone process, logs to stdout as JSON lines.
"""
import json, sys, time, traceback
from slack_sdk import WebClient
from slack_sdk.socket_mode import SocketModeClient
from slack_sdk.socket_mode.request import SocketModeRequest
from slack_sdk.socket_mode.response import SocketModeResponse

import os
BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN", "")
APP_TOKEN = os.environ.get("SLACK_APP_TOKEN", "")

bot = WebClient(token=BOT_TOKEN)

def handler(client, req):
    if req.type == "events_api":
        event = req.payload.get("event", {})
        et = event.get("type")
        resp = SocketModeResponse(envelope_id=req.envelope_id)
        client.send_socket_mode_response(resp)
        if et == "message" and event.get("channel_type") == "im" and not event.get("bot_id"):
            print(json.dumps({"type":"dm","user":event["user"],"text":event["text"],"channel":event["channel"]}), flush=True)
        elif et == "app_mention":
            print(json.dumps({"type":"mention","user":event["user"],"text":event["text"],"channel":event["channel"]}), flush=True)

def main():
    sys.stdout.reconfigure(line_buffering=True)
    print(json.dumps({"status":"starting"}), flush=True)
    client = SocketModeClient(app_token=APP_TOKEN, web_client=bot)
    client.socket_mode_request_listeners.append(handler)
    client.connect()
    print(json.dumps({"status":"connected"}), flush=True)
    while True:
        time.sleep(30)

if __name__ == "__main__":
    main()
