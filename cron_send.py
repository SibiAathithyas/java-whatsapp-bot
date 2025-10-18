# cron_send.py
# Used by Render's daily Cron Job to trigger your WhatsApp task

from app import send_daily_task

if __name__ == "__main__":
    send_daily_task()
