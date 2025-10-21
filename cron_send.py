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
    # Twilio creds from GitHub Secrets (provided by workflow)
    account_sid = os.environ["TWILIO_ACCOUNT_SID"]
    auth_token  = os.environ["TWILIO_AUTH_TOKEN"]
    from_num    = os.environ["TWILIO_WHATSAPP_FROM"]   # e.g. whatsapp:+14155238886 (sandbox)
    to_num      = os.environ["MY_WHATSAPP_TO"]         # e.g. whatsapp:+91XXXXXXXXXX

    client = Client(account_sid, auth_token)

    state = read_state()
    items = state["items"]
    day   = state["current_day"]

    FORCE = os.environ.get("FORCE_SEND") == "1"
    # Prevent double-send unless forced
    if not FORCE and state.get("last_sent_on") == today_ist():
        print("Already sent today. Exiting.")
        return

    key = str(day)
    if key not in items:
        body = "🎉 All tasks completed! Reply 'restart' to begin again."
    else:
        body = (
            f"{items[key]}\n\n"
            "Reply:\n"
            "• \"I'll do it\" ✅ to mark done\n"
            "• \"We'll do it tomorrow\" 🔁 to postpone\n"
            "• \"restart\" 🔄 to start from Day 1"
        )

    # Send via Twilio directly
    client.messages.create(from_=from_num, to=to_num, body=body)
    print("Message sent via Twilio.")

    # Mark sent for today
    state["last_sent_on"] = today_ist()
    write_state(state)
    print("State updated (last_sent_on).")

if __name__ == "__main__":
    main()
