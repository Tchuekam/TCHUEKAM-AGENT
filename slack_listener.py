"""
TCHUEKAM Slack Socket Mode Listener
Runs as a standalone process, logs to stdout as JSON lines.
"""
import json, sys, time, traceback, threading, os, uuid
from slack_sdk import WebClient
from slack_sdk.socket_mode import SocketModeClient
from slack_sdk.socket_mode.request import SocketModeRequest
from slack_sdk.socket_mode.response import SocketModeResponse

# Add tchuekam-agent/app to sys.path to import MiniSWERunner
sys.path.append(os.path.join(os.path.dirname(__file__), "tchuekam-agent", "app"))

BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN", "")
APP_TOKEN = os.environ.get("SLACK_APP_TOKEN", "")

bot = WebClient(token=BOT_TOKEN)

def run_swe_task(text, channel):
    try:
        from mini_swe_runner import MiniSWERunner
        runner = MiniSWERunner(
            env_type="docker",
            image="python:3.11-slim",
            cwd="/tmp/workspace",
            max_turns=30,
        )
        task_id = f"slack_{uuid.uuid4().hex[:6]}"
        bot.chat_postMessage(channel=channel, text=f"🤖 Acknowledged. Starting autonomous SWE task: {task_id}")
        
        result = runner.run_task(text, task_id=task_id)
        
        # Reply with the outcome
        status = "✅ Success" if result.get('success') else "❌ Failed"
        msg = f"Task {task_id} completed. {status}\nResult: {result.get('final_output')}"
        bot.chat_postMessage(channel=channel, text=msg)
    except Exception as e:
        bot.chat_postMessage(channel=channel, text=f"❌ Task failed to run: {e}")

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
            # Dispatch background SWE job
            t = threading.Thread(target=run_swe_task, args=(event["text"], event["channel"]))
            t.daemon = True
            t.start()

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
