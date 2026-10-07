import os
import requests
from fastapi import FastAPI, Request, Response, HTTPException
from dotenv import load_dotenv
from supabase import create_client, Client
from openai import OpenAI

# Load environment variables from .env file
load_dotenv()

# Initialize Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Initialize Llama (NVIDIA API)
LLAMA_API_KEY = os.getenv("LLAMA_API_KEY")
llama_client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=LLAMA_API_KEY
)

app = FastAPI(title="Voraus AI WhatsApp Bot")

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "voraus_ai_verify_token_123")
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN", "")

@app.get("/")
def read_root():
    return {"status": "Voraus AI WhatsApp Bot is running!"}

@app.get("/webhook")
def verify_webhook(request: Request):
    """
    Meta uses this endpoint to verify your webhook URL.
    It sends a GET request with hub.mode, hub.challenge, and hub.verify_token.
    """
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode and token:
        if mode == "subscribe" and token == VERIFY_TOKEN:
            print("WEBHOOK_VERIFIED")
            return Response(content=challenge, media_type="text/plain")
        else:
            raise HTTPException(status_code=403, detail="Verification token mismatch")
    raise HTTPException(status_code=400, detail="Missing parameters")

def get_ai_response(user_message: str) -> str:
    """
    Calls NVIDIA Llama 3.2 11B Instruct to get a response.
    """
    try:
        completion = llama_client.chat.completions.create(
            model="meta/llama-3.2-11b-vision-instruct",
            messages=[
                {"role": "system", "content": "You are Voraus AI, a helpful consultant for moving to Germany, assisting with university admissions, vocational training, and bureaucracy. Keep your answers concise, friendly, and formatted nicely for WhatsApp (use emojis, bold text like *this*, etc)."},
                {"role": "user", "content": user_message}
            ],
            temperature=0.5,
            max_tokens=512,
        )
        return completion.choices[0].message.content
    except Exception as e:
        print(f"Error calling Llama 3.2: {e}")
        return "Sorry, I'm having trouble connecting to my AI brain right now."

def send_whatsapp_message(phone_number_id: str, to: str, text: str):
    """
    Sends a text message using the WhatsApp Business API.
    """
    url = f"https://graph.facebook.com/v18.0/{phone_number_id}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": text}
    }
    
    response = requests.post(url, headers=headers, json=data)
    if response.status_code not in [200, 201]:
        print(f"Failed to send message: {response.text}")
    else:
        print(f"Message sent to {to} successfully.")

@app.post("/webhook")
async def handle_webhook(request: Request):
    """
    Meta sends WhatsApp messages to this endpoint via POST request.
    """
    body = await request.json()
    
    # Check if this is a WhatsApp message event
    if body.get("object"):
        entry = body.get("entry", [])
        if entry and entry[0].get("changes"):
            change = entry[0]["changes"][0]
            value = change.get("value", {})
            
            # Check if there are messages
            if value.get("messages"):
                message_data = value["messages"][0]
                sender_phone = message_data.get("from")
                message_type = message_data.get("type")
                
                print(f"\n--- New Message Received ---")
                print(f"From: {sender_phone}")
                print(f"Type: {message_type}")
                
                # Extract the phone number ID of the bot
                phone_number_id = value.get("metadata", {}).get("phone_number_id")

                if message_type == "text":
                    text_content = message_data["text"]["body"]
                    print(f"Content: {text_content}")
                    
                    # 1. Get AI Response from Llama 3.2
                    ai_reply = get_ai_response(text_content)
                    
                    # 2. Send the AI reply back via WhatsApp
                    send_whatsapp_message(phone_number_id, sender_phone, ai_reply)
                    
                    # 3. Store the chat in Supabase
                    try:
                        supabase.table("chat_history").insert({
                            "user_phone": sender_phone,
                            "user_message": text_content,
                            "ai_response": ai_reply
                        }).execute()
                        print("Saved chat to Supabase successfully.")
                    except Exception as e:
                        print(f"Note: Could not save to Supabase (Have you created the 'chat_history' table yet?): {e}")
                
        return Response(content="EVENT_RECEIVED", status_code=200)
    else:
        raise HTTPException(status_code=404, detail="Not Found")
