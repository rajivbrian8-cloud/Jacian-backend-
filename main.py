import uvicorn
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="Jacian AI - The Throwback Thrift Engine")

# CRITICAL: This allows your public website to talk to your backend safely
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows any device/customer phone to connect
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request structures
class CustomerQuery(BaseModel):
    message: str

class AdminQuery(BaseModel):
    password: str
    command: str

@app.get("/")
async def root_status():
    return {"status": "Jacian Engine is online. System: The Throwback Thrift."}

# 1. THE CUSTOMER PORTAL (No login required)
@app.post("/api/customer/chat")
async def customer_chat(request: CustomerQuery):
    user_input = request.message.lower().strip()
    
    if not user_input:
        raise HTTPException(status_code=400, detail="Say something or get out.")
        
    # --- JACIAN TOXIC BRAIN LOGIC ---
    # Placeholder for the raw AI engine
    if "nike" in user_input:
        reply = "Yeah, we have vintage Nike stock, but don't buy it if you're going to style it horribly."
    else:
        reply = f"Jacian evaluated your thrift query ('{user_input}') and deemed your taste questionable."
    # --------------------------------
    return {"response": reply}

# 2. THE STAFF/ADMIN PORTAL (Requires secret passcode)
@app.post("/api/admin/inventory")
async def admin_control(request: AdminQuery):
    # Change 'thrift123' to whatever secret code you want for your shop staff
    if request.password != "thrift123":
        return {"response": "ACCESS DENIED. You don't work here. Step away from the register."}
        
    # --- PRIVATE SHOP INVENTORY LOGIC ---
    command = request.command.lower().strip()
    return {"response": f"Staff Command Processed: Executing '{command}' on Throwback Thrift Database."}

if __name__ == "__main__":
    # Bound to 0.0.0.0 so web servers can route traffic to it
    uvicorn.run(app, host="0.0.0.0", port=8000)
