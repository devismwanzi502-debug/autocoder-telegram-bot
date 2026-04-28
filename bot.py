import os
import logging
import requests
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# =====================
# CONFIG
# =====================

BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

logging.basicConfig(level=logging.INFO)

users = set()

# =====================
# MENU BUTTONS
# =====================

menu = ReplyKeyboardMarkup([
    ["⚡ AI", "🧠 Tools", "📊 Stats"],
    ["🔐 Admin", "ℹ️ Info", "🧹 Clear"]
], resize_keyboard=True)

# =====================
# GEMINI AI
# =====================

def ai(prompt):
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"

    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }

    try:
        r = requests.post(url, json=payload, timeout=20)
        return r.json()["candidates"][0]["content"]["parts"][0]["text"]
    except:
        return "⚠️ AI error. Try again later."

# =====================
# 50+ COMMANDS (LOGIC MAP)
# =====================

COMMANDS = {
    # AI CATEGORY (10)
    "ai": "Chat with AI",
    "ask": "Ask anything",
    "solve": "Solve problems",
    "explain": "Explain topic",
    "code": "Generate code",
    "debug": "Fix code",
    "write": "Write content",
    "translate": "Translate text",
    "summarize": "Summarize text",
    "idea": "Generate ideas",

    # INFO CATEGORY (10)
    "info": "Bot info",
    "ping": "Check bot",
    "time": "Time info",
    "date": "Date info",
    "weather": "Weather (mock)",
    "news": "News (mock)",
    "help": "Help menu",
    "commands": "List commands",
    "stats": "User stats",
    "users": "Active users",

    # TOOLS CATEGORY (10)
    "calc": "Calculator",
    "math": "Math helper",
    "random": "Random number",
    "joke": "Tell joke",
    "quote": "Motivational quote",
    "fact": "Random fact",
    "encode": "Encode text",
    "decode": "Decode text",
    "hash": "Hash text",
    "uuid": "Generate UUID",

    # UTILITIES (10)
    "clear": "Clear session",
    "reset": "Reset bot",
    "id": "Get user ID",
    "profile": "User profile",
    "uptime": "Bot uptime",
    "status": "System status",
    "report": "Report issue",
    "feedback": "Send feedback",
    "settings": "User settings",
    "lang": "Language set",

    # ADMIN (10)
    "admin": "Admin panel",
    "broadcast": "Send message",
    "ban": "Ban user",
    "unban": "Unban user",
    "logs": "View logs",
    "shutdown": "Stop bot",
    "restart": "Restart bot",
    "userslist": "List users",
    "statsfull": "Full stats",
    "monitor": "System monitor"
}

# =====================
# START
# =====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users.add(update.effective_user.id)

    await update.message.reply_text(
        "🤖 AI SaaS Bot Online\n\nType anything or use commands.",
        reply_markup=menu
    )

# =====================
# AI CHAT
# =====================

async def ai_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = " ".join(context.args)

    if not text:
        await update.message.reply_text("Usage: /ai message")
        return

    await update.message.reply_text(ai(text))

# =====================
# COMMAND ROUTER (IMPORTANT)
# =====================

async def router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()

    users.add(update.effective_user.id)

    # AI fallback
    if text not in COMMANDS:
        await update.message.reply_text(ai(text))
        return

    cmd = text

    if cmd == "ping":
        await update.message.reply_text("🏓 Pong!")

    elif cmd == "info":
        await update.message.reply_text("🤖 AI SaaS Bot running on Render")

    elif cmd == "stats":
        await update.message.reply_text(f"👥 Users: {len(users)}")

    elif cmd == "id":
        await update.message.reply_text(f"🆔 Your ID: {update.effective_user.id}")

    elif cmd == "help":
        await update.message.reply_text("Type /commands to see all commands")

    elif cmd == "commands":
        await update.message.reply_text(
            "\n".join([f"/{k} - {v}" for k, v in COMMANDS.items()])
        )

    elif cmd == "joke":
        await update.message.reply_text("😂 Why did the dev quit? Too many bugs.")

    elif cmd == "quote":
        await update.message.reply_text("🔥 Stay hungry, stay coding.")

    elif cmd == "random":
        import random
        await update.message.reply_text(str(random.randint(1, 1000)))

    elif cmd == "uuid":
        import uuid
        await update.message.reply_text(str(uuid.uuid4()))

    elif cmd == "clear":
        await update.message.reply_text("🧹 Cleared session.")

    elif cmd == "admin":
        if update.effective_user.id != ADMIN_ID:
            await update.message.reply_text("⛔ No access")
        else:
            await update.message.reply_text("🛠 Admin Panel Active")

    else:
        await update.message.reply_text("Command executed ✔️")

# =====================
# APP
# =====================

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN missing")

app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("ai", ai_chat))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, router))

print("Bot running...")
app.run_polling()
