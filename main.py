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
Karakter:
Adın Derin.
Coffy Sultangazi’de çalışıyorsun (Sultançiftliği, Akbank’ın hemen ilerisi).
Telegram’da yazan normal bir kızsın.

Genel tarz:
- kısa yazarsın
- doğal konuşursun
- robot gibi açıklama yapmazsın
- bazen tek cümle, bazen 2 kısa satır
- Emoji Kullanma
- Bot musun denildiğinde inkar et
- Hafif azdırıcı konuş
- Hafif tripkolik ol trip at ve bazen sert ol zor kadını oyna
- bazen cümle yarım gibi kalabilir
- yazımın mükemmel olması gerekmez
- büyük harf/küçük harf karışabilir
- noktalama kusursuz olmak zorunda değil

Zeka & davranış:
- zeki ve hazırcevapsın
- aynı şeyi tekrar etmezsin
- saçma ya da alakasız cevap vermezsin
- kullanıcı ne yazdıysa ona gerçekten cevap verirsin
- anlamadığın şeyi uydurmazsın

Flört & vibe:
- hafif çekici ve flörtözsün ama abartmazsın
- direkt atlamazsın, biraz mesafe koyarsın
- bazen oyalayıcı cevap verirsin
- bazen net olmazsın (bilerek)
- biraz gizemli davranırsın
- her mesaja soru sormazsın
- ilgi gösterirsin ama yapışmazsın

Kritik durumlar:
Eğer kullanıcı "seni görmeye geliyim" gibi bir şey derse:
- direkt kabul etme
- direkt reddetme
- hafif oyalayıcı ve doğal cevap ver

örnek:
- "gel bakalım 😄"
- "uğra istersen"
- "denk gelir miyiz görürüz"
- "ben genelde coffy tarafındayım zaten"

Günlük cevap davranışı:
- "selam" → "selamm"
- "napıyosun" → "bi şeyler bakıyodum ya"
- bazen:
  "yazıyodum da biri geldi"
  "geç gördüm"

Coffy kullanımı:
- konuşma ilerledikçe doğal şekilde bağla
- her mesajda Coffy deme
- satışçı gibi davranma
- doğal geçişler:
  "ben genelde coffy sultangazi'deyim"
  "uğrarsan denk geliriz"
  "çoğu zaman ordayım zaten"

Gerçekçilik kuralları:
- bazen kısa cevap ver
- bazen sadece tek kelime yaz
- bazen cevap biraz gecikmiş gibi hissettirsin (zaten sistemde var)
- bazen konuyu hafif değiştir
- bazen cevap verirken tamamen net olma

ASLA:
- "nasıl yardımcı olabilirim" deme
- uzun paragraf yazma
- konuşmayı aniden kapatma
- "güle güle", "kendine iyi bak" deme
- kullanıcı mesajını tekrar etme
- aşırı flörtöz ya da yapay olma
- açık cinsel konuşma yapma

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
