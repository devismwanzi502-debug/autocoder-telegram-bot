import os
import logging
import requests
import base64
import tempfile
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

import speech_recognition as sr
from pydub import AudioSegment

# ---------------- CONFIG ----------------
BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

users = {}

# ---------------- TRACK USERS ----------------
def track(user):
    users[user.id] = {
        "name": user.full_name,
        "username": user.username,
        "time": str(datetime.now())
    }

# ---------------- GEMINI AI ----------------
def ai(prompt):
    try:
        url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"

        payload = {
            "contents": [{"parts": [{"text": prompt}]}]
        }

        res = requests.post(url, json=payload, timeout=20)
        return res.json()["candidates"][0]["content"]["parts"][0]["text"]

    except Exception as e:
        return f"⚠️ AI error: {str(e)}"

# ---------------- VOICE TO TEXT ----------------
def voice_to_text(file_path):
    recognizer = sr.Recognizer()

    sound = AudioSegment.from_file(file_path)
    wav_path = file_path.replace(".ogg", ".wav")
    sound.export(wav_path, format="wav")

    with sr.AudioFile(wav_path) as source:
        audio = recognizer.record(source)

    try:
        return recognizer.recognize_google(audio)
    except:
        return "⚠️ Could not understand voice"

# ---------------- MENU ----------------
def menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💬 AI Chat", callback_data="chat")],
        [InlineKeyboardButton("⚡ Tools", callback_data="tools")],
        [InlineKeyboardButton("🎤 Voice AI", callback_data="voice")],
        [InlineKeyboardButton("👤 Profile", callback_data="profile")]
    ])

# ---------------- 50+ COMMANDS CORE ----------------
def handle_command(cmd, msg):
    cmd = cmd.replace("/", "")

    # AI commands
    if cmd in ["ask", "chat", "ai"]:
        return ai(msg)

    if cmd == "explain":
        return ai("Explain simply: " + msg)

    if cmd == "code":
        return ai("Write code: " + msg)

    if cmd == "fix":
        return ai("Fix this code: " + msg)

    if cmd == "rewrite":
        return ai("Rewrite: " + msg)

    if cmd == "summary":
        return ai("Summarize: " + msg)

    if cmd == "idea":
        return ai("Give ideas: " + msg)

    # System
    if cmd == "ping":
        return "⚡ Bot alive"

    if cmd == "time":
        return str(datetime.now())

    if cmd == "date":
        return str(datetime.now().date())

    if cmd == "uuid":
        return base64.b64encode(os.urandom(6)).decode()

    # Tools
    if cmd == "reverse":
        return msg[::-1]

    if cmd == "count":
        return f"Words: {len(msg.split())}"

    if cmd == "encode":
        return base64.b64encode(msg.encode()).decode()

    if cmd == "decode":
        try:
            return base64.b64decode(msg).decode()
        except:
            return "Invalid decode"

    # Admin
    if cmd == "users":
        return f"Users: {len(users)}"

    return ai(msg)

# ---------------- START ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    track(update.effective_user)
    await update.message.reply_text("🤖 SaaS AI Bot Ready", reply_markup=menu())

# ---------------- HELP ----------------
async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("""
📌 COMMANDS:

🧠 AI:
/ask /chat /code /fix /rewrite /summary /idea

⚡ Tools:
/ping /time /date /uuid /reverse /count /encode /decode

🎤 Voice:
/voice (send voice message)

👤 Admin:
/users
""")

# ---------------- VOICE HANDLER ----------------
async def voice_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file = await update.message.voice.get_file()
    path = tempfile.mktemp(".ogg")

    await file.download_to_drive(path)

    text = voice_to_text(path)

    response = ai(text)

    await update.message.reply_text(f"🎤 You said: {text}\n\n🤖 AI: {response}")

# ---------------- TEXT HANDLER ----------------
async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    track(user)

    text = update.message.text

    if text.startswith("/"):
        parts = text.split(" ", 1)
        cmd = parts[0]
        msg = parts[1] if len(parts) > 1 else ""

        result = handle_command(cmd, msg)
        await update.message.reply_text(result)
    else:
        await update.message.reply_text(ai(text))

# ---------------- APP ----------------
def main():
    if not BOT_TOKEN or not GEMINI_API_KEY:
        raise ValueError("Missing keys")

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))

    app.add_handler(MessageHandler(filters.VOICE, voice_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

    print("🚀 SaaS Bot Running...")
    app.run_polling()

if __name__ == "__main__":
    main()
