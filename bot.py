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

# ===================== GEMINI AI (2.x FIXED + FALLBACK) =====================

def ask_ai(prompt):
    # 🔥 Try best available models in order
    models = [
        "gemini-2.5-flash",
        "gemini-2.0-flash",
        "gemini-2.0-pro"
    ]

    for model in models:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"

        payload = {
            "contents": [
                {"parts": [{"text": prompt}]}
            ]
        }

        try:
            res = requests.post(url, json=payload, timeout=25)
            data = res.json()

            # If success
            if "candidates" in data:
                return data["candidates"][0]["content"]["parts"][0]["text"]

            # If API error, try next model
            if "error" in data:
                logging.warning(f"Model {model} failed: {data['error'].get('message')}")

        except Exception as e:
            logging.warning(f"Model {model} crash: {str(e)}")

    return "⚠️ AI Error: All Gemini models failed or are unavailable for your API key."

# ===================== START =====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users.add(update.effective_user.id)

    await update.message.reply_text(
        "🤖 Welcome to X AI Bot\n\n"
        "✔ Gemini 2.x Connected\n"
        "✔ AI Chat Active\n"
        "✔ Tools Loaded",
        reply_markup=menu
    )

# ===================== BASIC COMMANDS =====================

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

    text = "👥 USERS:\n\n" + "\n".join(str(u) for u in list(users)[:50])
    await update.message.reply_text(text)

# ===================== AI COMMAND =====================

async def ai_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = " ".join(context.args)

    if not text:
        return await update.message.reply_text("Usage: /ai hello")

    await update.message.reply_text(ask_ai(text))

# ===================== CHAT HANDLER =====================

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users.add(update.effective_user.id)

    user_text = update.message.text
    reply = ask_ai(user_text)

    await update.message.reply_text(reply)

# ===================== APP =====================

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN missing")

app = ApplicationBuilder().token(BOT_TOKEN).build()

# Commands
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("ping", ping))
app.add_handler(CommandHandler("stats", stats))
app.add_handler(CommandHandler("id", user_id))
app.add_handler(CommandHandler("admin", admin))
app.add_handler(CommandHandler("users", users_cmd))
app.add_handler(CommandHandler("ai", ai_command))

# Chat handler (LAST)
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

print("🤖 Bot running with Gemini 2.x...")
app.run_polling()
