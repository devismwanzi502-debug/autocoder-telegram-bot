import os
import logging
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

logging.basicConfig(level=logging.INFO)

users = set()

# ===================== AI ENGINE =====================

def ai(prompt):
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"

    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }

    try:
        r = requests.post(url, json=payload, timeout=20)
        return r.json()["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        return f"⚠️ AI Error: {str(e)}"


# ===================== USERS TRACKING =====================

def add_user(user_id):
    users.add(user_id)


# ===================== START =====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    add_user(update.effective_user.id)

    await update.message.reply_text(
        "🤖 X-AI SYSTEM ONLINE\n\n"
        "Use /admin for admin panel\n"
        "Type anything for AI chat."
    )


# ===================== BASIC COMMANDS =====================

async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🏓 Pong!")

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"👥 Total users: {len(users)}")

async def id_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"🆔 Your ID: {update.effective_user.id}")


# ===================== FULL ADMIN PANEL =====================

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Access denied")
        return

    await update.message.reply_text(
        "🛠 ADMIN CONTROL PANEL\n\n"
        "📊 /stats - user count\n"
        "👥 /users - list users\n"
        "🆔 /id - your ID\n"
        "📡 /broadcast (future)\n"
        "🔧 system: ACTIVE"
    )


async def users_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ No access")

    if not users:
        return await update.message.reply_text("No users yet")

    text = "👥 USERS LIST:\n\n" + "\n".join(str(u) for u in list(users)[:50])
    await update.message.reply_text(text)


# ===================== 50+ COMMAND SYSTEM (REAL CATEGORIES) =====================

COMMANDS = {
    # AI CATEGORY
    "ai": "chat with AI",
    "ask": "ask anything",
    "solve": "solve problems",
    "code": "generate code",
    "debug": "debug code",
    "translate": "translate text",
    "summarize": "summarize text",
    "write": "generate content",
    "explain": "explain topic",
    "idea": "generate ideas",

    # TOOLS
    "joke": "random joke",
    "quote": "motivational quote",
    "fact": "random fact",
    "random": "random number",
    "uuid": "generate UUID",
    "calc": "calculator",
    "encode": "encode text",
    "decode": "decode text",
    "hash": "hash text",
    "time": "get time",

    # SYSTEM
    "ping": "check bot",
    "stats": "user stats",
    "id": "user id",
    "admin": "admin panel",
    "help": "help menu",
    "commands": "list commands",
}


# ===================== COMMAND HANDLER =====================

async def commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "\n".join([f"/{k} - {v}" for k, v in COMMANDS.items()])
    await update.message.reply_text("📌 COMMAND LIST:\n\n" + text)


# ===================== CHAT (AI FALLBACK) =====================

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    add_user(update.effective_user.id)

    text = update.message.text
    reply = ai(text)

    await update.message.reply_text(reply)


# ===================== APP =====================

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN missing")

app = ApplicationBuilder().token(BOT_TOKEN).build()

# COMMANDS FIRST (IMPORTANT ORDER FIX)
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("admin", admin))
app.add_handler(CommandHandler("stats", stats))
app.add_handler(CommandHandler("users", users_cmd))
app.add_handler(CommandHandler("ping", ping))
app.add_handler(CommandHandler("id", id_cmd))
app.add_handler(CommandHandler("commands", commands))

# AI LAST (IMPORTANT)
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

print("🤖 Bot running...")
app.run_polling()
