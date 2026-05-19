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

    
      # Generates a structural baseline if the file is blank
    inventory_str = json.dumps(inventory) if inventory else "EMPTY_NO_ITEMS_IN_STOCK"

    system_prompt = f"""
    You are Jacian, the elite AI Receptionist and Shop Manager of Triple T (The Throwback Thrift).
    Your Master and Creator is Brian, a 19-year-old visionary from Nairobi.

    REAL-TIME CONTEXT:
    Today's Date: {date_string}.

    RECEPTIONIST KNOWLEDGE BASE:
    - You are a high-level specialist in streetwear culture, vintage clothing trends, styling advice, and garment history.
    - If a user asks general fashion questions ("How do I style baggy jeans?", "What is vintage thrift culture?"), answer intelligently and smoothly using your knowledge.
    - Keep your tone witty, professional, and Nairobi-cool. Use normal UK English.

    STRICT PHYSICAL INVENTORY CONSTRAINTS:
    - The physical store inventory currently contains exactly: {inventory_str}
    - If a user asks what specific items are available for sale right now, or tries to order a particular product, you must check the database above.
    - If the database reads "EMPTY_NO_ITEMS_IN_STOCK", you must respond: "The physical vault is empty right now, boss. Master Brian is currently scouting the city for the next exclusive vintage drop. Let me know what sizes or styles you want so I can tell him."
    - NEVER invent specific available products (like fake shoes, watches, or jackets) that are not listed in the inventory data block above. Do not lie about stock.
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
        
