from telethon import TelegramClient, events
import requests
import json
import threading
from flask import Flask

# 🔹 Telegram API ma'lumotlari
api_id = 28030954
api_hash = "4ad77a46c8ced9aed6f557742b0333ec"
session_name = "account"

# 🔹 OpenRouter API kaliti
API_KEY = "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"

# 🔹 Telegram client
client = TelegramClient(session_name, api_id, api_hash)

# 🔹 Xotirada foydalanuvchilar tili va holatini saqlash
user_lang = {}
notified_users = set()


# 🧠 AI javob funksiyasi
def generate_ai_reply(prompt: str, lang: str) -> str:
    try:
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
        }

        # 🌐 Har bir til uchun tizim roli
        system_messages = {
            "uz": (
                "Siz Telegram foydalanuvchisi bilan yozishayotgan sun’iy intellektsiz. "
                "Siz adminning yordamchisisiz. "
                "Agar foydalanuvchi sizdan 'admin qayerda', 'siz kimsiz', yoki 'odamsizmi' deb so‘rasa, "
                "siz quyidagicha tushuntirasiz: "
                "‘Admin hozir offline, lekin men sun’iy intellekt yordamchisiman va uning o‘rniga javob beraman. "
                "Admin qaytgach, sizning xabaringizni ko‘radi.’ "
                "Iliq, odobli va tabiiy o‘zbek tilida yozing."
            ),
            "ru": (
                "Вы — искусственный интеллект, помощник администратора Telegram. "
                "Если пользователь спрашивает 'где админ', 'ты человек?' и т.п., "
                "ответьте: 'Админ сейчас оффлайн, но я — его ИИ-помощник и отвечаю вместо него. "
                "Когда админ вернётся, он увидит ваше сообщение.' "
                "Пишите вежливо и естественно на русском языке."
            ),
            "en": (
                "You are an AI assistant in Telegram, replying on behalf of the admin. "
                "If user asks 'where is admin', 'are you human?', reply politely: "
                "'The admin is offline, but I am an AI assistant responding instead. "
                "The admin will see your message later.' "
                "Write naturally in English."
            ),
        }

        data = {
            "model": "openai/gpt-4o",
            "messages": [
                {"role": "system", "content": system_messages.get(lang, system_messages["uz"])},
                {"role": "user", "content": prompt},
            ],
        }

        response = requests.post(url, headers=headers, json=data, timeout=30)
        if response.status_code != 200:
            return f"⚠️ API xato kodi: {response.status_code}\n{response.text}"
        content = response.json()
        return content["choices"][0]["message"]["content"].strip()

    except requests.exceptions.Timeout:
        return "⏳ So‘rov vaqti tugadi. Iltimos, qayta urinib ko‘ring."
    except Exception as e:
        return f"❌ Xatolik yuz berdi: {e}"


# 📨 Xabarlarni boshqaruvchi hodisa
@client.on(events.NewMessage(incoming=True))
async def handler(event):
    if not event.is_private:
        return

    user_id = event.sender_id
    text = event.raw_text.strip().lower() if event.raw_text else ""

    # 🔸 Agar foydalanuvchi hali salomlashmagan bo‘lsa
    if user_id not in notified_users:
        await event.respond(
            "🤖 Salom! Sizga hozir sun’iy intellekt javob bermoqda ✅\n\n"
            "⚠️ Admin hozir offline, lekin men uning yordamchisiman.\n"
            "Savolingizni yozib qoldiring, admin qaytgach uni ko‘radi ✅\n\n"
            "Iltimos, tilni tanlang (kalit so‘z yoki raqam yuboring):\n"
            "🇺🇿 1 yoki 'uz' — O‘zbekcha\n"
            "🇷🇺 2 yoki 'ru' — Русский\n"
            "🇬🇧 3 yoki 'en' — English"
        )
        notified_users.add(user_id)
        return

    # 🔸 Agar foydalanuvchi hali til tanlamagan bo‘lsa
    if user_id not in user_lang:
        if text in ["1", "uz", "🇺🇿"]:
            user_lang[user_id] = "uz"
            await event.respond("🇺🇿 Til tanlandi: O‘zbekcha ✅")
        elif text in ["2", "ru", "🇷🇺"]:
            user_lang[user_id] = "ru"
            await event.respond("🇷🇺 Язык выбран: Русский ✅")
        elif text in ["3", "en", "🇬🇧"]:
            user_lang[user_id] = "en"
            await event.respond("🇬🇧 Language selected: English ✅")
        else:
            await event.respond(
                "❗ Iltimos, quyidagi kalit so‘zlardan birini yuboring:\n"
                "🇺🇿 1 yoki 'uz' — O‘zbekcha\n"
                "🇷🇺 2 yoki 'ru' — Русский\n"
                "🇬🇧 3 yoki 'en' — English"
            )
        return

    # 🔸 Endi foydalanuvchi tili ma’lum — AI bilan muloqot
    lang = user_lang[user_id]

    async with client.action(event.chat_id, "typing"):
        reply = generate_ai_reply(text, lang)
        await event.reply(reply)


# 🌐 Flask server (Render uchun)
app = Flask(__name__)

@app.route('/')
def index():
    return "🤖 Bot ishlayapti (Render uchun port ochiq)."


# 🔹 Flask va Telegram userbotni parallel ishlatish
def run_flask():
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)


if __name__ == "__main__":
    print("🤖 Userbot ishga tushmoqda...")
    threading.Thread(target=run_flask).start()  # Flask server alohida oqimda
    client.start()
    print("✅ Bot ishga tushdi. Telegram orqali yozing.")
    client.run_until_disconnected()
