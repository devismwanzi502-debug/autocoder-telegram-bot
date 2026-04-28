import os
import logging
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

# ======================
# LOGGING (IMPORTANT)
# ======================
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# ======================
# ENV VARIABLES
# ======================
BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not BOT_TOKEN:
    raise ValueError("Missing BOT_TOKEN in environment")

if not GEMINI_API_KEY:
    raise ValueError("Missing GEMINI_API_KEY in environment")

# ======================
# SIMPLE MEMORY (SESSION)
# ======================
user_memory = {}

# ======================
# GEMINI CALL
# ======================
def ask_gemini(prompt: str):
    try:
        url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"

        payload = {
            "contents": [
                {"parts": [{"text": prompt}]}
            ]
        }

        res = requests.post(url, json=payload, timeout=20)
        return res.json()

    except Exception as e:
        return {"error": str(e)}

# ======================
# MENU BUTTONS
# ======================
def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💬 Chat AI", callback_data="chat")],
        [InlineKeyboardButton("📜 Help", callback_data="help")],
        [InlineKeyboardButton("📊 Status", callback_data="status")]
    ])

# ======================
# START
# ======================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to AutoCoder AI Bot v2\nChoose below:",
        reply_markup=main_menu()
    )

# ======================
# HELP
# ======================
async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🧠 Commands:\n"
        "/start - menu\n"
        "/help - help\n"
        "/ping - check bot\n"
        "/clear - reset memory\n\n"
        "💬 Just type anything to chat with AI"
    )
    await update.message.reply_text(text)

# ======================
# PING
# ======================
async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Bot is alive and running")

# ======================
# CLEAR MEMORY
# ======================
async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_memory.pop(update.effective_user.id, None)
    await update.message.reply_text("🧹 Memory cleared")

# ======================
# CALLBACK MENU HANDLER
# ======================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "help":
        await query.edit_message_text(
            "🧠 Help Menu\nUse /help or just chat with AI"
        )

    elif query.data == "chat":
        await query.edit_message_text("💬 Just send a message to chat with AI")

    elif query.data == "status":
        await query.edit_message_text("📊 Bot is running normally 🚀")

# ======================
# CHAT HANDLER (AI)
# ======================
async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    # store memory
    if user_id not in user_memory:
        user_memory[user_id] = []

    user_memory[user_id].append(text)
    last_context = "\n".join(user_memory[user_id][-5:])

    prompt = f"User chat history:\n{last_context}\n\nUser: {text}\nAI:"

    data = ask_gemini(prompt)

    try:
        reply = data["candidates"][0]["content"]["parts"][0]["text"]
    except:
        reply = "⚠ AI error. Try again later."

    await update.message.reply_text(reply)

# ======================
# ERROR HANDLER
# ======================
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logging.error(f"Error: {context.error}")

# ======================
# MAIN
# ======================
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("ping", ping))
    app.add_handler(CommandHandler("clear", clear))

    # menu buttons
    app.add_handler(CallbackQueryHandler(button_handler))

    # chat
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

    app.add_error_handler(error_handler)

    print("🤖 AutoCoder Bot v2 running...")
    app.run_polling()

if __name__ == "__main__":
    main()
