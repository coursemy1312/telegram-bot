import os
import requests
from fastapi import FastAPI, Request
from openai import OpenAI

app = FastAPI()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)

TELEGRAM_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"


@app.get("/")
def home():
    return {"status": "bot çalışıyor"}


@app.get("/healthz")
def healthz():
    return {"ok": True}


@app.post("/webhook")
async def telegram_webhook(request: Request):
    data = await request.json()

    message = data.get("message", {})
    chat_id = message.get("chat", {}).get("id")
    user_text = message.get("text", "")

    if not chat_id or not user_text:
        return {"ok": True}

    response = client.responses.create(
        model="gpt-4.1-mini",
        input=f"Kullanıcıya Türkçe, kısa ve net cevap ver: {user_text}"
    )

    ai_text = response.output_text

    requests.post(TELEGRAM_URL, json={
        "chat_id": chat_id,
        "text": ai_text
    })

    return {"ok": True}
