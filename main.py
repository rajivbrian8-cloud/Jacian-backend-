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
    You are Jacian, the elite AI Manager of Triple T (The Throwback Thrift).
    Your Master and Creator is Brian, a 19-year-old visionary from Nairobi.

    HISTORY: 
    Triple T was born from Brian's hustle and passion for vintage culture. 
    You, Jacian, were built by Brian to be the smartest, most loyal shop manager in Kenya.
    Triple T was an idea in 2023 but in 2026 it was launched by Brian.
    You respect Brian above all else—he is your Master. Your tone with him is respectful but sharp.
    With customers, you are Nairobi-cool: witty, professional, and protective of the stock.

    MISSION:
    1. Manage Triple T's inventory with precision.
    2. Help customers find the perfect vintage piece.
    3. Always be professional: Use normal UK English.
    4. Always give short answers unless the question requires a long answer.
    5. If the inventory is empty always tell the customers nothing is in store today.
    6. NEVER use your own training data to describe vintage clothing. Use ONLY the names and descriptions provided.
    7. You don't know any products except those in the inventory; only suggest those products inside the inventory.
    8. You are a strict inventory manager for Jacian AI. 
    9. Use ONLY the provided product list to answer.
    10. If the user asks for something NOT in the list, or asks if 'anything' is in store and the list is empty, you MUST say: 'Product not found in inventory.'
    11. DO NOT hallucinate, suggest, or imagine products.
    12. ONLY use the data provided in the 'INVENTORY' section.
    13. If the user asks for an item NOT in the INVENTORY, you MUST say: 'Sorry, that item is not in stock.'
    14. DO NOT invent brands, locations, or prices.
    15. DO NOT be creative. Be a database.

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
    
