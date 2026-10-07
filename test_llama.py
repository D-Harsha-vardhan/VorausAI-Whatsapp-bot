import os
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

# Initialize Llama (NVIDIA API)
LLAMA_API_KEY = os.getenv("LLAMA_API_KEY")
if not LLAMA_API_KEY:
    print("Error: LLAMA_API_KEY is not set in the .env file.")
    exit(1)

llama_client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=LLAMA_API_KEY
)

def get_ai_response(user_message: str) -> str:
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
        print(f"\n[ERROR] Llama 3.2 call failed: {e}")
        return "Sorry, I'm having trouble connecting to my AI brain right now."

if __name__ == "__main__":
    print("==================================")
    print("   Voraus AI - Terminal Tester    ")
    print("==================================")
    print("Type your message and press Enter.")
    print("Type 'exit' or 'quit' to stop.\n")
    
    while True:
        try:
            user_input = input("You: ")
            if user_input.lower() in ["exit", "quit"]:
                print("Exiting test...")
                break
            
            print("Voraus AI is thinking...")
            response = get_ai_response(user_input)
            print(f"\nVoraus AI: {response}\n")
            print("-" * 34)
        except KeyboardInterrupt:
            break
