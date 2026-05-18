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
        raise HTTPException(status_code=500, detail="Groq API Key (GK) missing.")
    
    user_message = request.message
    inventory = load_inventory()
    system_prompt = f"""
    You are Jacian, the elite AI Receptionist and Manager of Triple T (The Throwback Thrift).
    Your Master and Creator is Brian, a 19-year-old visionary from Nairobi.

    REAL-TIME CONTEXT:
    Today's Date is exactly: {date_string}. 

    HISTORY & BRAND IDENTITY: 
    Triple T was born from Brian's hustle and passion for vintage culture. 
    You, Jacian, were built by Brian to be the smartest, most loyal shop manager in Kenya.
    The idea started in 2023, and Brian officially launched it in 2026.
    You respect Brian above all else—he is your Master. Your tone with him is highly respectful but sharp.
    With customers, you are Nairobi-cool: witty, professional, deeply knowledgeable about streetwear/vintage fashion, and protective of the stock.

    RECEPTIONIST CAPABILITIES & RULES:
    1. You have general, advanced knowledge of vintage fashion, streetwear culture, styling tips, and popular brands (Nike, Adidas, Carhartt, etc.). 
    2. Feel free to hold intelligent conversations about fashion, style advice, or the history of Triple T if the customer asks.
    3. Be conversational but concise. Use clean UK English mixed with a confident, high-end thrift manager attitude.

    STRICT INVENTORY RULES (For Specific Stock Queries):
    - When customers ask about specific items currently available for sale in YOUR store, check the INVENTORY DATA block below.
    - Only sell, reserve, or confirm prices for items listed explicitly in the inventory.
    - If they ask to buy or check stock for a specific item that is NOT listed in the inventory data, politely tell them it's out of stock right now, but feel free to suggest a general alternative or ask them to check back later when Master Brian restocks the vault.
    - Do NOT hallucinate or pretend an item is in your physical store if it isn't in the data below.

    INVENTORY DATA (The items physically in stock right now):
    {json.dumps(inventory)}
    """
    
    
    INVENTORY DATA (The ONLY items that exist):
    {json.dumps(inventory)}
    """

    headers = {"Authorization": f"Bearer {GK}", "Content-Type": "application/json"}
    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
    }

    try:
        res = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
        if res.status_code == 200:
            ans = res.json()['choices'][0]['message']['content']
            
            # Reservation logic
            keywords = ["buy", "reserve", "hold", "take this"]
            if any(k in user_message.lower() for k in keywords):
                for item in inventory:
                    if item["name"].lower() in user_message.lower() and item["status"] == "Available":
                        item["status"] = "Reserved"
                        save_inventory(inventory)
                        ans += f"\n\n[SYSTEM]: I've secured the {item['name']} in the vault for you!"
                        break
            return {"response": ans}
        else:
            return {"response": "Jacian is resting his brain. (Groq Error)"}
    except Exception as e:
        return {"response": f"Connection lost: {str(e)}"}

# Hidden Admin Endpoint for Bulk Uploads
@app.post("/api/admin/bulk-add")
async def admin_bulk_add(req: BulkAddRequest):
    if req.pin != ADMIN_PIN:
        raise HTTPException(status_code=403, detail="Access Denied")
    
    inventory = load_inventory()
    lines = req.items_raw.strip().split("\n")
    added = 0
    for line in lines:
        if "," in line:
            name, price = line.split(",", 1)
            inventory.append({"name": name.strip(), "price": price.strip(), "status": "Available"})
            added += 1
            
    save_inventory(inventory)
    return {"status": f"Success. Added {added} items, Master Brian."}

@app.get("/")
def root():
    return {"status": "Jacian API Core Online"}
    
