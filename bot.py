import os
import json
import logging
import requests
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# ===================== CONFIG =====================

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

logging.basicConfig(level=logging.INFO)

DB_FILE = "kernel_v13.json"

users = set()
user_state = {}

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
            "memory": [],
            "mode": "HOME"
        }
        save_db()

def add_memory(uid, text):
    db[str(uid)]["memory"].append(text)
    db[str(uid)]["memory"] = db[str(uid)]["memory"][-15:]
    save_db()

# ===================== AI ENGINE =====================

def ai(prompt, uid):

    url = "https://api.groq.com/openai/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    system = """
You are AI KERNEL v13.
You are a helpful assistant inside a Telegram app UI.
Be structured, short, and useful.
"""

    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt}
        ]
    }

    try:
        res = requests.post(url, json=payload, headers=headers, timeout=25)
        data = res.json()
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        return f"⚠️ ERROR: {str(e)}"

# ===================== BUTTON MENUS =====================

HOME_MENU = ReplyKeyboardMarkup([
    ["🧠 AI HUB", "📚 LEARN HUB"],
    ["💻 DEV HUB", "🧰 TOOLS HUB"],
    ["🎮 FUN HUB", "👑 ADMIN"]
], resize_keyboard=True)

AI_MENU = ReplyKeyboardMarkup([
    ["💬 Chat AI", "🧠 Deep Think"],
    ["🔍 Explain", "🧩 Explore"],
    ["⬅️ Back"]
], resize_keyboard=True)

LEARN_MENU = ReplyKeyboardMarkup([
    ["📖 Learn", "🧪 Science"],
    ["💰 Business", "⬅️ Back"]
], resize_keyboard=True)

DEV_MENU = ReplyKeyboardMarkup([
    ["💻 Code", "🐞 Debug"],
    ["⚙️ System Design", "⬅️ Back"]
], resize_keyboard=True)

TOOLS_MENU = ReplyKeyboardMarkup([
    ["🛠 Utilities", "📊 Info"],
    ["📂 Help", "⬅️ Back"]
], resize_keyboard=True)

FUN_MENU = ReplyKeyboardMarkup([
    ["😂 Joke", "🎮 Ideas"],
    ["🎭 Story", "⬅️ Back"]
], resize_keyboard=True)

# ===================== START =====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    users.add(uid)
    init_user(uid)

    await update.message.reply_text(
        "🤖 AI KERNEL v13 ONLINE\nButton OS activated.",
        reply_markup=HOME_MENU
    )

# ===================== ADMIN =====================

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ NO ACCESS")

    await update.message.reply_text(
        f"""
👑 ADMIN PANEL

Users: {len(users)}
Memory nodes: {len(db)}
"""
    )

# ===================== CHAT ENGINE =====================

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):

    uid = update.effective_user.id
    users.add(uid)
    init_user(uid)

    text = update.message.text

    # ================= MAIN HUBS =================

    if text == "🧠 AI HUB":
        return await update.message.reply_text("AI Hub", reply_markup=AI_MENU)

    if text == "📚 LEARN HUB":
        return await update.message.reply_text("Learning Hub", reply_markup=LEARN_MENU)

    if text == "💻 DEV HUB":
        return await update.message.reply_text("Dev Hub", reply_markup=DEV_MENU)

    if text == "🧰 TOOLS HUB":
        return await update.message.reply_text("Tools Hub", reply_markup=TOOLS_MENU)

    if text == "🎮 FUN HUB":
        return await update.message.reply_text("Fun Hub", reply_markup=FUN_MENU)

    if text == "👑 ADMIN":
        return await admin(update, context)

    if text == "⬅️ Back":
        return await update.message.reply_text("Main Menu", reply_markup=HOME_MENU)

    # ================= AI ACTIONS =================

    if text == "💬 Chat AI":
        return await update.message.reply_text("Send any message to chat.")

    if text == "🧠 Deep Think":
        return await update.message.reply_text(ai("solve deeply step by step", uid))

    if text == "🔍 Explain":
        return await update.message.reply_text(ai("explain clearly and simply", uid))

    if text == "🧩 Explore":
        return await update.message.reply_text(ai("creative exploration mode", uid))

    # ================= LEARN =================

    if text == "📖 Learn":
        return await update.message.reply_text(ai("teach topic simply", uid))

    if text == "🧪 Science":
        return await update.message.reply_text(ai("science explanations", uid))

    if text == "💰 Business":
        return await update.message.reply_text(ai("business ideas and startup plans", uid))

    # ================= DEV =================

    if text == "💻 Code":
        return await update.message.reply_text(ai("act as senior programmer", uid))

    if text == "🐞 Debug":
        return await update.message.reply_text(ai("debug code problems", uid))

    if text == "⚙️ System Design":
        return await update.message.reply_text(ai("system architecture design", uid))

    # ================= TOOLS =================

    if text == "🛠 Utilities":
        return await update.message.reply_text(ai("useful tools and utilities", uid))

    if text == "📊 Info":
        return await update.message.reply_text(ai("general information assistant", uid))

    if text == "📂 Help":
        return await update.message.reply_text("This is your AI OS. Use buttons.")

    # ================= FUN =================

    if text == "😂 Joke":
        return await update.message.reply_text(ai("tell jokes", uid))

    if text == "🎮 Ideas":
        return await update.message.reply_text(ai("game ideas", uid))

    if text == "🎭 Story":
        return await update.message.reply_text(ai("creative story", uid))

    # ================= DEFAULT AI =================

    reply = ai(text, uid)
    add_memory(uid, text)

    await update.message.reply_text(reply)

# ===================== RUN =====================

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN missing")

app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("admin", admin))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

print("🤖 AI KERNEL v13 BUTTON OS RUNNING...")
app.run_polling()
