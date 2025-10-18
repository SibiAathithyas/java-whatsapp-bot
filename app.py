import os, json, datetime
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from dotenv import load_dotenv
from pytz import timezone

# Load env
load_dotenv()
ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
FROM = os.getenv("TWILIO_WHATSAPP_FROM")
TO = os.getenv("MY_WHATSAPP_TO")
DAILY_HOUR_IST = int(os.getenv("DAILY_HOUR_IST", "17"))  # default 5 PM IST
IST = timezone("Asia/Kolkata")
TASKS_FILE = "tasks.json"

client = Client(ACCOUNT_SID, AUTH_TOKEN)
app = Flask(__name__)

# ---------- State helpers ----------
def read_state():
    with open(TASKS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def write_state(state):
    with open(TASKS_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)

def today_ist():
    return datetime.datetime.now(IST).strftime("%Y-%m-%d")

def total_days(state):
    return max(map(int, state["items"].keys()))

def send(body):
    client.messages.create(from_=FROM, to=TO, body=body)

# ---------- Core behaviors ----------
def send_daily_task():
    """Send today's task once per IST calendar day."""
    state = read_state()
    day = state["current_day"]
    items = state["items"]

    if str(day) not in items:
        send("🎉 All tasks completed! Reply 'restart' to begin again.")
        return

    if state.get("last_sent_on") == today_ist():
        return  # already sent today

    task = items[str(day)]
    msg = (
        f"👋 Hey Sibi!\n"
        f"📚 {task}\n\n"
        f"Reply with:\n"
        f"• \"I'll do it\" ✅ to mark done\n"
        f"• \"We'll do it tomorrow\" 🔁 to postpone (shifts plan)\n"
        f"• \"restart\" 🔄 to start from Day 1"
    )
    send(msg)
    state["last_sent_on"] = today_ist()
    write_state(state)

def mark_done():
    """Complete today and advance to next day."""
    state = read_state()
    state["streak"] = state.get("streak", 0) + 1

    if state["current_day"] < total_days(state):
        state["current_day"] += 1
        state["last_sent_on"] = ""  # allow next day's send
        write_state(state)
        send(
            f"✅ Nice job! Streak: {state['streak']}🔥\n"
            f"Next task will come tomorrow at 5 PM IST."
        )
    else:
        write_state(state)
        send(f"🏁 You’ve finished all tasks! Final streak: {state['streak']}.")

def snooze():
    """
    Postpone today's task to tomorrow and shift the plan forward (no piling).
    Keep current_day unchanged; we’ll resend it tomorrow at the scheduled time.
    """
    state = read_state()
    state["last_sent_on"] = ""  # so it can resend tomorrow
    write_state(state)
    send("🔁 Got it! Task postponed — I’ll resend it tomorrow at 5 PM IST 🌙")

def restart():
    """Reset progress to Day 1."""
    state = read_state()
    state["current_day"] = 1
    state["streak"] = 0
    state["last_sent_on"] = ""
    write_state(state)
    send("🔄 Restarted from Day 1! Let’s begin again strong 💪")

# ---------- Webhook ----------
@app.route("/whatsapp", methods=["POST"])
def whatsapp_webhook():
    incoming = (request.values.get("Body") or "").strip().lower()
    resp = MessagingResponse()

    # Normalize smart quotes by mapping curly to straight (helps matching)
    normalized = (
        incoming
        .replace("’", "'")
        .replace("‘", "'")
        .replace("“", '"')
        .replace("”", '"')
    )

    if any(p in normalized for p in ["i'll do it", "ill do it", "i ll do it"]):
        mark_done()
        resp.message("Marked as done. 💪")
    elif any(p in normalized for p in [
        "we'll do it tomorrow", "well do it tomorrow", "we ll do it tomorrow"
    ]):
        snooze()
        resp.message("Okay—postponed to tomorrow 🌙")
    elif normalized.strip() == "restart":
        restart()
        resp.message("Restarted. 🚀")
    else:
        resp.message(
            "Commands:\n"
            "• \"I'll do it\" → mark done\n"
            "• \"We'll do it tomorrow\" → postpone\n"
            "• \"restart\" → start from Day 1"
        )
    return str(resp)

# ---------- Scheduler ----------
scheduler = BackgroundScheduler(timezone=IST)
scheduler.start()
scheduler.add_job(
    send_daily_task,
    trigger=CronTrigger(hour=DAILY_HOUR_IST, minute=0, second=0, timezone=IST),
    id="daily_task",
    replace_existing=True
)

# ---------- Run ----------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
