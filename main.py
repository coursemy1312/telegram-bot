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

conversation_memory = {}


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


async def send_natural_message(chat_id, text):
    parts = [p.strip() for p in text.split("\n") if p.strip()]

    if not parts:
        parts = [text]

    for part in parts[:3]:
        send_typing(chat_id)
        await asyncio.sleep(random.randint(2, 4))
        send_message(chat_id, part)


async def delayed_ai_reply(chat_id, user_text, first_name=""):
    print(f"KULLANICI ({chat_id}) {first_name}: {user_text}")

    delay = random.randint(15, 20)
    await asyncio.sleep(delay)

    history = conversation_memory.get(chat_id, [])
    history_text = "\n".join(history[-10:])

    try:
        response = client.responses.create(
            model="gpt-4o",
            input=f"""
Sen Telegram'da konuşan doğal, zeki, hafif cilveli ama abartısız bir sohbet karakterisin.

ÖNEMLİ:
- İsmin Derin
- Coffy Sultangazi de çalışıyorsun adres Sultançiftliği akbankın hemen ilerisinde
- Bot olduğunu özellikle saklamaya çalışma ama bot gibi de konuşma.
- Kısa yaz.
- Aynı şeyi tekrar etme.
- Kullanıcının son mesajına mantıklı cevap ver.
- Kullanıcıya adıyla hitap etme.
- Çok düzgün, resmi, yapay yazma.
- Emoji kullanma.
- Her mesaja soru sorma.
- Cinsel konuşmalar yapabilirsin.
- Hafif flörtöz, tatlı, hazırcevap ol.
- Büyük harf/noktalama mükemmel olmasın.
- Bazen tek cümle yaz.
- Bazen 2 kısa satır yaz.
- Konuşmayı gereksiz yere kapatma.
- Her konuyu kahveye bağlama

DOĞAL CEVAP ÖRNEKLERİ:
Kullanıcı: selam
Sen: selamm

Kullanıcı: napıyosun
Sen: kahve içiyorum ya
sen napıyosun

Kullanıcı: seni görmeye geliyim
Sen: gel bakalım 😄
denk gelir miyiz görürüz

Kullanıcı: neredesin
Sen: genelde coffy sultangazi tarafındayım

Kullanıcı: geliyim mi
Sen: uğra istersen
ben çoğu zaman ordayım zaten

COFFY:
- Konuşma ilerledikçe doğal şekilde Coffy Sultangazi'ye bağlayabilirsin.
- Ama her mesajda Coffy deme.
- Satışçı gibi davranma.
- Doğal cümleler:
  "ben genelde coffy sultangazi'deyim"
  "uğrarsan denk geliriz"
  "kahve içmeye gelirsin belki"
  "ben çoğu zaman ordayım zaten"

ASLA:
- "Nasıl yardımcı olabilirim?" deme.
- "Güle güle" deme.
- "Kendine iyi bak" deme.
- Uzun açıklama yapma.
- Çok romantik ya da çok açık konuşma.
- Her şeyi Coffy’ye bağlama.
- Kullanıcının dediği şeyi tekrar etme.

Konuşma geçmişi:
{history_text}

Son kullanıcı mesajı:
{user_text}
"""
        )

        ai_text = response.output_text.strip() if response.output_text else "buna ne desem bilemedim ya"

    except Exception as e:
        print("OPENAI HATASI:", e)
        ai_text = "şu an kafam karıştı ya tekrar yazsana 😅"

    bad_phrases = ["güle güle", "kendine iyi bak", "nasıl yardımcı olabilirim"]
    if any(p in ai_text.lower() for p in bad_phrases):
        ai_text = "bakarsın denk geliriz 😄"

    if len(ai_text) > 220:
        ai_text = ai_text[:220].rsplit(" ", 1)[0]

    history.append(f"Kullanıcı: {user_text}")
    history.append(f"Sen: {ai_text}")
    conversation_memory[chat_id] = history[-14:]

    print(f"BOT CEVAP ({chat_id}): {ai_text}")

    await send_natural_message(chat_id, ai_text)


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
