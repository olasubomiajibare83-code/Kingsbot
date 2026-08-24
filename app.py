import os
from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel

app = FastAPI()

# Your AI API key will come from Hugging Face Secrets.
# NEVER put the actual key directly in this file.
AI_API_KEY = os.getenv("AI_API_KEY")


class ChatRequest(BaseModel):
    message: str
    history: list = []


@app.get("/")
async def home():
    return FileResponse("index.html")


@app.get("/health")
async def health():
    return {
        "status": "online",
        "ai_key_configured": bool(AI_API_KEY)
    }


@app.post("/chat")
async def chat(request: ChatRequest):

    user_message = request.message.strip()

    if not user_message:
        return {
            "reply": "Please type a message."
        }

    # We will connect the real AI model here next.
    #
    # For now, this confirms that the frontend
    # can successfully communicate with the backend.

    return {
        "reply": (
            "🧠 My AI brain is connected to the backend, "
            "but the actual AI model still needs to be connected."
        )
    }
