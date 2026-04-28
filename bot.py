import os
import logging
import requests
import json
from telegram import (
    Update,
    ReplyKeyboardMarkup,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    CallbackQueryHandler,
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
            "messages": []
        }
        save_db()

def add_xp(uid):
    user = db[str(uid)]
    user["xp"] += 1

    if user["xp"] >= user["level"] * 5:
        user["xp"] = 0
        user["level"] += 1

    save_db()

def add_memory(uid, text):
    db[str(uid)]["messages"].append(text)
    db[str(uid)]["messages"] = db[str(uid)]["messages"][-10:]
    save_db()

def get_memory(uid):
    return " | ".join(db[str(uid)]["messages"])

# ===================== UI =====================

menu = ReplyKeyboardMarkup([
    ["🤖 AI Chat", "👑 Admin Panel"],
    ["🧑‍💻 Level"]
], resize_keyboard=True)

admin_menu = InlineKeyboardMarkup([
    [InlineKeyboardButton("📊 Stats", callback_data="stats")],
    [InlineKeyboardButton("👥 Users", callback_data="users")],
    [InlineKeyboardButton("🏓 Ping", callback_data="ping")],
    [InlineKeyboardButton("🔙 Close", callback_data="back")]
])

# ===================== AI ENGINE =====================

cache = {}

def ask_ai(prompt, uid):

    init_user(uid)
    add_xp(uid)

    if prompt in cache:
        return cache[prompt]

    memory = get_memory(uid)
    level = db[str(uid)]["level"]

    final_prompt = f"""
User Level: {level}

Memory:
{memory}

User:
{prompt}

Respond clearly and naturally.
"""

    url = "https://api.groq.com/openai/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": final_prompt}]
    }

    try:
        res = requests.post(url, json=payload, headers=headers, timeout=25)
        data = res.json()

        if "error" in data:
            return f"⚠️ AI Error: {data['error'].get('message', 'Unknown')}"

        reply = data["choices"][0]["message"]["content"]

        cache[prompt] = reply
        add_memory(uid, prompt)

        return reply

    except Exception as e:
        return f"⚠️ AI Crash: {str(e)}"

# ===================== START =====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    init_user(uid)

    await update.message.reply_text(
        "🤖 X AI SYSTEM ONLINE\n\nWelcome!",
        reply_markup=menu
    )

# ===================== LEVEL =====================

async def level(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    init_user(uid)

    lvl = db[str(uid)]["level"]
    xp = db[str(uid)]["xp"]

    await update.message.reply_text(
        f"🧑‍💻 Level: {lvl}\n⚡ XP: {xp}/{lvl * 5}"
    )

# ===================== ADMIN =====================

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ Access Denied")

    await update.message.reply_text("👑 Admin Panel", reply_markup=admin_menu)

# ===================== BUTTONS =====================

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    uid = q.from_user.id

    if q.data == "stats":
        await q.edit_message_text(f"👥 Users: {len(db)}")

    elif q.data == "users":
        if uid != ADMIN_ID:
            return await q.edit_message_text("⛔ No access")

        text = "👥 USERS:\n\n" + "\n".join(list(db.keys())[:50])
        await q.edit_message_text(text)

    elif q.data == "ping":
        await q.edit_message_text("🏓 Pong!")

    elif q.data == "back":
        await q.edit_message_text("👑 Closed")

# ===================== CHAT =====================

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    init_user(uid)

    text = update.message.text

    if text == "🤖 AI Chat":
        return await update.message.reply_text("💬 Send anything...")

    if text == "👑 Admin Panel":
        return await admin(update, context)

    if text == "🧑‍💻 Level":
        return await level(update, context)

    reply = ask_ai(text, uid)
    await update.message.reply_text(reply)

# ===================== APP =====================

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN missing")

app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("admin", admin))
app.add_handler(CommandHandler("level", level))

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))
app.add_handler(CallbackQueryHandler(buttons))

print("🤖 Bot running...")
app.run_polling()
