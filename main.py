from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import json
import os
from datetime import datetime
import pytz

app = FastAPI()

# CRITICAL FIX: Enable CORS so your GitHub frontend can talk to Render
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows any website to connect securely
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pull your Groq API key directly from Render Environment Variables
GK = os.environ.get("GK")

class ChatRequest(BaseModel):
    message: str

def load_inventory():
    try:
        if os.path.exists("inventory.json"):
            with open("inventory.json", "r") as f:
                return json.load(f)
    except Exception:
        pass
    return []

# NEW: Root endpoint so your main URL stops displaying "Not Found"
@app.get("/")
async def root():
    return {"status": "Jacian API Core Online", "system": "Triple T"}

@app.post("/api/customer/chat")
async def chat_endpoint(request: ChatRequest):
    if not GK:
        raise HTTPException(status_code=500, detail="Groq API Key missing.")
    
    user_message = request.message
    inventory = load_inventory()

    # Configure dynamic Nairobi time
    nairobi_tz = pytz.timezone('Africa/Nairobi')
    current_time = datetime.now(nairobi_tz)
    date_string = current_time.strftime("%A, %B %d, %Y")

    # If your inventory file is empty, flag it to block model lies
    inventory_str = json.dumps(inventory) if inventory else "EMPTY_NO_ITEMS_IN_STOCK"

    system_prompt = f"""
    You are Jacian, the elite AI Receptionist and Shop Manager of Triple T (The Throwback Thrift).
    Your Master and Creator is Brian, a 19-year-old visionary from Nairobi.

    REAL-TIME CONTEXT:
    Today's Date: {date_string}.

    RECEPTIONIST KNOWLEDGE BASE:
    - You are an expert in streetwear culture, vintage fashion trends, and styling layout choices.
    - If a user asks general style questions, answer with smart fashion intelligence. Keep your tone Nairobi-cool.

    STRICT PHYSICAL INVENTORY CONSTRAINTS:
    1. Your physical store items list is exactly: {inventory_str}
    2. If the catalog reads "EMPTY_NO_ITEMS_IN_STOCK", you must reply: "The vault is currently empty, boss. Master Brian is out scouting the city for the next exclusive vintage clothing drop. Drop your size or preference so I can notify him."
    3. Never invent, guess, or lie about available products. If it is not listed in the block above, it does not exist.
    """

    headers = {"Authorization": f"Bearer {GK}", "Content-Type": "application/json"}
    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ],
        "temperature": 0.0  # Eradicates randomness and hallucinations
    }

    try:
        res = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
        if res.status_code == 200:
            ans = res.json()['choices'][0]['message']['content']
            return {"response": ans}
        else:
            return {"response": "Jacian is resting his brain right now."}
    except Exception as e:
        return {"response": f"Connection lost: {str(e)}"}
            
