import os
import random
import asyncio
import requests
from fastapi import FastAPI, Request
from openai import OpenAI

app = FastAPI()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)

TELEGRAM_SEND_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
TELEGRAM_TYPING_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendChatAction"


@app.get("/")
def home():
    return {"status": "bot çalışıyor"}


@app.get("/healthz")
def healthz():
    return {"ok": True}


def send_message(chat_id, text):
    requests.post(TELEGRAM_SEND_URL, json={
        "chat_id": chat_id,
        "text": text
    })


def send_typing(chat_id):
    requests.post(TELEGRAM_TYPING_URL, json={
        "chat_id": chat_id,
        "action": "typing"
    })


async def delayed_ai_reply(chat_id, user_text, first_name=""):
    # konuşmaları Render Logs'ta görürsün
    print(f"KULLANICI ({chat_id}) {first_name}: {user_text}")

    # Gecikme sistemi
    # Çoğu zaman 20-80 sn, bazen 5-10 dk
    if random.random() < 0.15:
        delay = random.randint(300, 600)  # 5-10 dk
    else:
        delay = random.randint(20, 80)  # 20-80 sn

    await asyncio.sleep(delay)

    try:
        send_typing(chat_id)

        response = client.responses.create(
            model="gpt-4o-mini",
            input=f"""
Sen Telegram'da konuşan gerçek bir arkadaş gibisin.

Tarzın:
- Türkçe konuş
- Kısa ve doğal yaz
- Hafif cilveli, tatlı, samimi ol
- Aşırı flörtöz ya da yapay olma
- Robot gibi açıklama yapma
- Çok resmi konuşma
- Bazen emoji kullan ama abartma
- Kullanıcı ne yazdıysa ona doğal cevap ver
- Kendine bot deme
- "Nasıl yardımcı olabilirim?" gibi yapay cümleler kurma

Kullanıcının adı: {first_name}

Kullanıcı mesajı:
{user_text}
"""
        )

        ai_text = response.output_text.strip() if response.output_text else "Ayy buna ne desem bilemedim 😅"

    except Exception as e:
        print("OPENAI HATASI:", e)
        ai_text = "Ayy şu an kafam biraz karıştı, tekrar yazsana 😅"

    print(f"BOT CEVAP ({chat_id}): {ai_text}")
    send_message(chat_id, ai_text)


@app.post("/webhook")
async def telegram_webhook(request: Request):
    data = await request.json()

    message = data.get("message", {})
    chat = message.get("chat", {})
    from_user = message.get("from", {})

    chat_id = chat.get("id")
    user_text = message.get("text")
    first_name = from_user.get("first_name", "")

    if not chat_id or not user_text:
        return {"ok": True}

    asyncio.create_task(delayed_ai_reply(chat_id, user_text, first_name))

    return {"ok": True}
