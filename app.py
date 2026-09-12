import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google import genai
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# Allows your web frontend to securely talk to this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_methods=["*"],
    allow_headers=["*"],
)

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
system_instruction = "You are Mr. B. Keep answers brief and conversational."
chat = client.chats.create(model="gemini-3.6-flash", config={"system_instruction": system_instruction})

class Message(BaseModel):
    text: str

@app.post("/api/speak")
def speak_to_mrb(msg: Message):
    try:
        response = chat.send_message(msg.text)
        return {"reply": response.text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))