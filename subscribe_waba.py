import os
import sys
import requests
from dotenv import load_dotenv

load_dotenv()

WABA_ID = "1130162983003323"
TOKEN = os.getenv("WHATSAPP_TOKEN")

if not TOKEN:
    print("Error: WHATSAPP_TOKEN not found in .env")
    sys.exit(1)

url = f"https://graph.facebook.com/v18.0/{WABA_ID}/subscribed_apps"
headers = {
    "Authorization": f"Bearer {TOKEN}"
}

print(f"Subscribing App to WABA ID: {WABA_ID}...")
response = requests.post(url, headers=headers)

if response.status_code == 200:
    print("Success! Your WhatsApp Business Account is now subscribed to the webhook.")
else:
    print(f"Failed! Error: {response.text}")
