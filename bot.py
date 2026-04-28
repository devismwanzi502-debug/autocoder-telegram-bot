import os
import logging
import requests
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# =========================
# CONFIG
# =========================

BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN missing")

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY missing")

URL = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"

# =========================
# MEMORY (simple runtime)
# =========================

users = set()
banned = set()

# =========================
# LOGGING
# =========================

logging.basicConfig(level=logging.INFO)

# =========================
# AI FUNCTION
# =========================

def ask_ai(text: str) -> str:
    try:
        payload = {
            "contents": [{"parts": [{"text": text}]}]
        }
        res = requests.post(URL, json=payload, timeout=20)
        data = res.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        logging.error(e)
        return "⚠️ AI error. Try again."

# =========================
# BUTTON MENU (CATEGORIES)
# =========================

menu = ReplyKeyboardMarkup(
    [
        ["💬 AI Chat", "📚 Education"],
        ["🧠 Coding", "🧰 Tools"],
        ["🎮 Fun", "⚡ Utilities"],
        ["🛠 Admin Panel"]
    ],
    resize_keyboard=True
)

# =========================
# START
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    users.add(uid)

    await update.message.reply_text(
        "🤖 *AI BOT ONLINE*\nChoose a category:",
        reply_markup=menu,
        parse_mode="Markdown"
    )

# =========================
# ADMIN PANEL
# =========================

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ No access")
        return

    await update.message.reply_text(
        "🛠 ADMIN PANEL\n\n"
        "/stats - bot stats\n"
        "/broadcast msg - send to all\n"
        "/ban id\n"
        "/unban id"
    )

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    await update.message.reply_text(
        f"📊 STATS\nUsers: {len(users)}\nBanned: {len(banned)}"
    )

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    msg = " ".join(context.args)
    for u in users:
        if u not in banned:
            try:
                await context.bot.send_message(u, f"📢 {msg}")
            except:
                pass

    await update.message.reply_text("✅ Sent")

async def ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    try:
        uid = int(context.args[0])
        banned.add(uid)
        await update.message.reply_text(f"⛔ Banned {uid}")
    except:
        await update.message.reply_text("Usage: /ban id")

async def unban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    try:
        uid = int(context.args[0])
        banned.discard(uid)
        await update.message.reply_text(f"✅ Unbanned {uid}")
    except:
        await update.message.reply_text("Usage: /unban id")

# =========================
# MESSAGE ROUTER (CATEGORIES)
# =========================

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    uid = update.effective_user.id

    users.add(uid)

    if uid in banned:
        await update.message.reply_text("⛔ You are banned.")
        return

    # ================= CATEGORIES =================

    if text == "💬 AI Chat":
        await update.message.reply_text("💬 Send anything to chat with AI.")
        return

    if text == "📚 Education":
        await update.message.reply_text(
            "📚 Topics:\n- Math\n- Science\n- History\n- English"
        )
        return

    if text == "🧠 Coding":
        await update.message.reply_text(
            "🧠 Coding Help:\n- Python\n- JavaScript\n- HTML\n- Debugging"
        )
        return

    if text == "🧰 Tools":
        await update.message.reply_text(
            "🧰 Tools:\n- Calculator\n- Converter\n- Search"
        )
        return

    if text == "🎮 Fun":
        await update.message.reply_text(
            "🎮 Fun Mode:\n- Jokes\n- Facts\n- Games"
        )
        return

    if text == "⚡ Utilities":
        await update.message.reply_text(
            "⚡ Utilities:\n- Time\n- Weather\n- Notes"
        )
        return

    if text == "🛠 Admin Panel":
        await admin(update, context)
        return

    # ================= AI RESPONSE =================

    reply = ask_ai(text)
    await update.message.reply_text(reply)

# =========================
# COMMANDS
# =========================

async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⚡ Alive")

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "/start - menu\n/ping - test\n/admin - admin panel"
    )

# =========================
# MAIN
# =========================

app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("ping", ping))
app.add_handler(CommandHandler("help", help_cmd))

app.add_handler(CommandHandler("admin", admin))
app.add_handler(CommandHandler("stats", stats))
app.add_handler(CommandHandler("broadcast", broadcast))
app.add_handler(CommandHandler("ban", ban))
app.add_handler(CommandHandler("unban", unban))

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

print("🤖 Bot running...")
app.run_polling()
