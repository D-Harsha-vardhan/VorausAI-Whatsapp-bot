import os
import requests
from fastapi import FastAPI, Request, Response, HTTPException, BackgroundTasks
from dotenv import load_dotenv
from supabase import create_client, Client as SupabaseClient
from openai import OpenAI
from twilio.rest import Client as TwilioClient

# Load environment variables from .env file
load_dotenv()

# Initialize Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
supabase: SupabaseClient = create_client(SUPABASE_URL, SUPABASE_KEY)

# Initialize Llama (NVIDIA API)
LLAMA_API_KEY = os.getenv("LLAMA_API_KEY")
llama_client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=LLAMA_API_KEY
)

app = FastAPI(title="Voraus AI WhatsApp Bot")

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_WHATSAPP_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER", "whatsapp:+14155238886")

@app.get("/")
def read_root():
    return {"status": "Voraus AI WhatsApp Bot is running!"}

@app.get("/whatsapp")
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
        return completion.choices[0].message.content or ""
    except Exception as e:
        print(f"Error calling Llama 3.2: {e}")
        return "Sorry, I'm having trouble connecting to my AI brain right now."

def send_whatsapp_message(to: str, text: str):
    """
    Sends a text message using the Twilio WhatsApp API.
    """
    if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN:
        print("Twilio credentials not configured.")
        return
        
    twilio_client = TwilioClient(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    try:
        message = twilio_client.messages.create(
            from_=TWILIO_WHATSAPP_NUMBER,
            body=text,
            to=to
        )
        print(f"Message sent to {to} successfully. SID: {message.sid}")
    except Exception as e:
        print(f"Failed to send message: {e}")

def process_whatsapp_message(sender_phone: str, text_content: str):
    # 1. Get AI Response from Llama 3.2
    ai_reply = get_ai_response(text_content)
    
    # 2. Send the AI reply back via WhatsApp
    send_whatsapp_message(sender_phone, ai_reply)
    
    # 3. Store the chat in Supabase
    try:
        supabase.table("chat_history").insert({
            "user_phone": sender_phone,
            "user_message": text_content,
            "ai_response": ai_reply
        }).execute()
        print("Saved chat to Supabase successfully.")
    except Exception as e:
        print(f"Note: Could not save to Supabase: {e}")

@app.post("/whatsapp")
async def handle_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Twilio sends WhatsApp messages to this endpoint via POST request with Form Data.
    """
    form_data = await request.form()
    
    sender_phone = form_data.get("From")
    text_content = form_data.get("Body")
    
    if sender_phone and text_content:
        print(f"\n--- New Message Received ---")
        print(f"From: {sender_phone}")
        print(f"Content: {text_content}")
        
        # Schedule the AI processing in the background
        background_tasks.add_task(
            process_whatsapp_message, 
            sender_phone, 
            text_content
        )
            
    return Response(content="EVENT_RECEIVED", status_code=200)
