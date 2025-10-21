# cron_send.py — send today's task directly via Twilio (no host needed)

import os, json, datetime
from twilio.rest import Client
from pytz import timezone

TASKS_FILE = "tasks.json"
IST = timezone("Asia/Kolkata")

def today_ist():
    return datetime.datetime.now(IST).strftime("%Y-%m-%d")

def read_state():
    with open(TASKS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def write_state(state):
    with open(TASKS_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)

def main():
    # Twilio creds from GitHub Secrets (in the workflow env)
    account_sid = os.environ["TWILIO_ACCOUNT_SID"]
    auth_token  = os.environ["TWILIO_AUTH_TOKEN"]
    from_num    = os.environ["TWILIO_WHATSAPP_FROM"]
    to_num      = os.environ["MY_WHATSAPP_TO"]

    client = Client(account_sid, auth_token)

    state = read_state()
    items = state["items"]
    day   = state["current_day"]

    # prevent double send on the same IST date
    if state.get("last_sent_on") == today_ist():
        print("Already sent today. Exiting.")
        return

    key = str(day)
    if key not in items:
        body = "🎉 All tasks completed! Reply 'restart' to begin again."
    else:
        # Build the message body
        title = items[key].split("\n", 1)[0]  # first line as title
        body  = f"👋 Hey Sibi!\n{items[key]}\n\nReply:\n• \"I'll do it\" ✅ to mark done\n• \"We'll do it tomorrow\" 🔁 to postpone\n• \"restart\" 🔄 to start from Day 1"

    # Send via Twilio directly
    client.messages.create(from_=from_num, to=to_num, body=body)

    # Mark sent for today so cron won't resend
    state["last_sent_on"] = today_ist()
    write_state(state)
    print("Message sent and state updated.")

if __name__ == "__main__":
    main()
