import os
import logging
import requests
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# ===================== CONFIG =====================

BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

logging.basicConfig(level=logging.INFO)

users = set()

# ===================== MENU =====================

menu = ReplyKeyboardMarkup([
    ["🤖 AI Chat", "📚 Education"],
    ["🧠 Coding", "🛠 Tools"],
    ["🎮 Fun", "⚡ Utilities"],
    ["👑 Admin Panel"]
], resize_keyboard=True)

# ===================== GEMINI AI (FIXED) =====================

def ask_ai(prompt):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"

    payload = {
        "contents": [
            {"parts": [{"text": prompt}]}
        ]
    }

    try:
        res = requests.post(url, json=payload, timeout=25)
        data = res.json()

        if "error" in data:
            return f"⚠️ AI Error: {data['error'].get('message', 'Unknown error')}"

        return data["candidates"][0]["content"]["parts"][0]["text"]

    except Exception as e:
        return f"⚠️ AI Crash: {str(e)}"

# ===================== START =====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users.add(update.effective_user.id)

    await update.message.reply_text(
        "🤖 Welcome to X AI Bot\n\n"
        "✔ AI Chat Active\n"
        "✔ Tools Ready",
        reply_markup=menu
    )

# ===================== BASIC =====================

async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🏓 Pong!")

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"👥 Users: {len(users)}")

async def user_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"🆔 ID: {update.effective_user.id}")

# ===================== ADMIN =====================

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ Access Denied")

    await update.message.reply_text(
        "👑 ADMIN PANEL\n\n"
        "/stats - users\n"
        "/users - list users\n"
        "/ping - test bot"
    )

async def users_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ No access")

    if not users:
        return await update.message.reply_text("No users yet")

    await update.message.reply_text("👥 USERS:\n" + "\n".join(str(u) for u in list(users)[:50]))

# ===================== AI COMMAND =====================

async def ai_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = " ".join(context.args)

    if not text:
        return await update.message.reply_text("Usage: /ai hello")

    await update.message.reply_text(ask_ai(text))

# ===================== CHAT =====================

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users.add(update.effective_user.id)

    reply = ask_ai(update.message.text)
    await update.message.reply_text(reply)

# ===================== BOOT =====================

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN missing")

app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("ping", ping))
app.add_handler(CommandHandler("stats", stats))
app.add_handler(CommandHandler("id", user_id))
app.add_handler(CommandHandler("admin", admin))
app.add_handler(CommandHandler("users", users_cmd))
app.add_handler(CommandHandler("ai", ai_command))

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

print("🤖 Bot running...")
app.run_polling()
