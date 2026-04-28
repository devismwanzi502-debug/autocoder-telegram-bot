import os
import json
import logging
import requests
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

# ===================== CONFIG =====================

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

logging.basicConfig(level=logging.INFO)

DB_FILE = "db.json"

# ===================== DATABASE =====================

def load_db():
    try:
        with open(DB_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_db():
    with open(DB_FILE, "w") as f:
        json.dump(db, f)

db = load_db()

def init_user(uid):
    if str(uid) not in db:
        db[str(uid)] = {
            "xp": 0,
            "level": 1,
            "memory": []
        }
        save_db()

def add_memory(uid, text):
    db[str(uid)]["memory"].append(text)
    db[str(uid)]["memory"] = db[str(uid)]["memory"][-10:]
    save_db()

def get_memory(uid):
    return " | ".join(db[str(uid)]["memory"])

def add_xp(uid):
    user = db[str(uid)]
    user["xp"] += 1

    if user["xp"] >= user["level"] * 5:
        user["xp"] = 0
        user["level"] += 1

    save_db()

# ===================== AI ENGINE =====================

def ask_ai(prompt, uid):

    init_user(uid)
    add_xp(uid)

    memory = get_memory(uid)
    level = db[str(uid)]["level"]

    system_prompt = f"""
You are an advanced AI system inside a Telegram bot.

User Level: {level}

User Memory:
{memory}

IMPORTANT TASK:
Generate useful, creative responses OR suggest dynamic categories when asked.

User Message:
{prompt}
"""

    url = "https://api.groq.com/openai/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": system_prompt}]
    }

    try:
        res = requests.post(url, json=payload, headers=headers, timeout=25)
        data = res.json()

        if "error" in data:
            return f"⚠️ AI Error: {data['error'].get('message', 'Unknown')}"

        reply = data["choices"][0]["message"]["content"]

        add_memory(uid, prompt)

        return reply

    except Exception as e:
        return f"⚠️ AI Crash: {str(e)}"

# ===================== MAIN MENU =====================

menu = ReplyKeyboardMarkup([
    ["🤖 AI HUB"],
    ["⚡ Generate Menu"]
], resize_keyboard=True)

# ===================== START =====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    init_user(uid)

    await update.message.reply_text(
        "🤖 DYNAMIC AI SYSTEM ONLINE\n\nNo fixed categories — AI creates everything.",
        reply_markup=menu
    )

# ===================== DYNAMIC MENU GENERATOR =====================

async def generate_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id

    prompt = """
Create 6 creative Telegram bot categories.
Each category must be short (1-2 words only).
Make them unique, futuristic, and useful.
Return ONLY the list.
"""

    result = ask_ai(prompt, uid)

    # convert AI output into buttons
    items = result.split("\n")
    items = [i.strip("-• ") for i in items if i.strip()]

    keyboard = [[item] for item in items[:6]]

    await update.message.reply_text(
        "⚡ AI GENERATED MENU:",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )

# ===================== AI HUB =====================

async def ai_hub(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("💬 Talk to AI directly — no limits.")

# ===================== CHAT =====================

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    init_user(uid)

    text = update.message.text

    if text == "🤖 AI HUB":
        return await ai_hub(update, context)

    if text == "⚡ Generate Menu":
        return await generate_menu(update, context)

    reply = ask_ai(text, uid)
    await update.message.reply_text(reply)

# ===================== APP =====================

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN missing")

app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

print("🤖 Dynamic AI Bot Running...")
app.run_polling()
