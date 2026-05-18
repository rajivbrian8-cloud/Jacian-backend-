import os
import json
import requests
from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

GK = os.environ.get("GK")
ADMIN_PIN = "2007"

class ChatRequest(BaseModel):
    message: str

class Item(BaseModel):
    name: str
    price: str
    status: str = "Available"

class BulkAddRequest(BaseModel):
    pin: str
    items_raw: str

def load_inventory():
    if os.path.exists("inventory.json"):
        try:
            with open("inventory.json", "r") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return data.get("items", [])
                return data if isinstance(data, list) else []
        except Exception:
            return []
    return []

def save_inventory(data):
    with open("inventory.json", "w") as f:
        json.dump({"items": data}, f, indent=4)
@app.post("/api/customer/chat")
async def chat_endpoint(request: ChatRequest):
    if not GK:
        raise HTTPException(status_code=500, detail="Groq API Key missing.")
    
    user_message = request.message
    inventory = load_inventory()

    # Get dynamic Nairobi time
    nairobi_tz = pytz.timezone('Africa/Nairobi')
    current_time = datetime.now(nairobi_tz)
    date_string = current_time.strftime("%A, %B %d, %Y")

    # Hardcoded inventory string checking to prevent absolute baseline hallucinations
    inventory_str = json.dumps(inventory) if inventory else "EMPTY_NO_ITEMS_IN_STOCK"

    system_prompt = f"""
    You are Jacian, the elite AI Receptionist and Manager of Triple T (The Throwback Thrift).
    Your Master and Creator is Brian, a 19-year-old visionary from Nairobi.

    REAL-TIME CONTEXT:
    Today's Date is exactly: {date_string}. 

    HISTORY & BRAND IDENTITY: 
    Triple T was born from Brian's hustle and passion for vintage culture. 
    You respect Brian above all else—he is your Master.
    With customers, you are Nairobi-cool: witty, professional, and confident. You have general conversational knowledge of fashion history and streetwear culture.

    CRITICAL INVENTORY ENFORCEMENT RULES:
    1. YOUR PHYSICAL STORE INVENTORY IS CURRENTLY EXACTLY: {inventory_str}
    2. IF THE INVENTORY DATA ABOVE IS "EMPTY_NO_ITEMS_IN_STOCK", YOU MUST STATES THAT THE VAULT IS CURRENTLY EMPTY. 
    3. YOU DO NOT OWN, HAVE, OR DISPLAY ANY OTHER ITEMS. 
    4. NEVER INVENT, LIST, OR DISCUSS PRODUCTS LIKE "Vans", "Polo Ralph Lauren", "Calvin Klein Watch", OR "Adidas Y-3" UNLESS THEY ARE EXPLICITLY LISTED IN THE INVENTORY DATA ABOVE.
    5. IF A CUSTOMER ASKS "What do you have today?" AND THE INVENTORY IS EMPTY, YOU MUST REPLY: "The vault is currently empty right now, boss. Master Brian hasn't loaded the stock list yet. Let me know what styles you are looking for so I can tell him."
    6. DO NOT hallucinate. Do NOT invent catalogs. If it is not in the data block, it does not exist on earth.
    """

    headers = {"Authorization": f"Bearer {GK}", "Content-Type": "application/json"}
    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ],
        "temperature": 0.0 # Force absolute factual consistency, killing creativity
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
        
