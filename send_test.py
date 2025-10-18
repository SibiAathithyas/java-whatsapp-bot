import os
from twilio.rest import Client
from dotenv import load_dotenv

load_dotenv()

account_sid = os.getenv("TWILIO_ACCOUNT_SID")
auth_token = os.getenv("TWILIO_AUTH_TOKEN")
from_whatsapp = os.getenv("TWILIO_WHATSAPP_FROM")
to_whatsapp = os.getenv("MY_WHATSAPP_TO")

client = Client(account_sid, auth_token)

message = client.messages.create(
    from_=from_whatsapp,
    to=to_whatsapp,
    body="👋 Hey Sibi! This is your Java Study Bot test message. Everything’s working perfectly! 🚀"
)

print("✅ Message sent successfully!")
print("Message SID:", message.sid)
