import os
import json
import logging
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# ===================== CONFIG =====================

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

logging.basicConfig(level=logging.INFO)

DB_FILE = "agent_db.json"

users = set()

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
            "tasks": [],
            "goals": [],
            "mode": "AUTONOMOUS"
        }
        save_db()

def add_memory(uid, text):
    db[str(uid)]["memory"].append(text)
    db[str(uid)]["memory"] = db[str(uid)]["memory"][-15:]
    save_db()

def add_task(uid, task):
    db[str(uid)]["tasks"].append(task)
    db[str(uid)]["tasks"] = db[str(uid)]["tasks"][-10:]
    save_db()

def add_goal(uid, goal):
    db[str(uid)]["goals"].append(goal)
    db[str(uid)]["goals"] = db[str(uid)]["goals"][-10:]
    save_db()

# ===================== INTELLIGENCE LAYER =====================

def intelligence_layer(uid, text):
    return f"""
You are an autonomous AI agent.

User: {text}

Memory:
{db[str(uid)]['memory']}

Goals:
{db[str(uid)]['goals']}

Tasks:
{db[str(uid)]['tasks']}

Decide:
- normal response
- TASK:
- PLAN:
Be structured and intelligent.
"""

# ===================== AI ENGINE =====================

def ai(prompt, uid):

    init_user(uid)

    system = """
You are AI AUTONOMOUS AGENT v10.

You are a structured reasoning system.

Rules:
- respond smartly
- or output TASK:
- or output PLAN:
- never be random
"""

    url = "https://api.groq.com/openai/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

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

# ===================== START =====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    users.add(uid)
    init_user(uid)

    await update.message.reply_text(
        "🤖 AUTONOMOUS AI AGENT v10 ONLINE\n\nAdmin + autonomy system active."
    )

# ===================== ADMIN PANEL =====================

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ ACCESS DENIED")

    await update.message.reply_text(
        f"""
👑 ADMIN PANEL

👥 Users: {len(users)}

Commands:
/stats
/users
/ping
"""
    )

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:
        return

    await update.message.reply_text(f"👥 Total Users: {len(users)}")

async def list_users(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:
        return

    text = "\n".join(str(u) for u in list(users)[:50])
    await update.message.reply_text(f"👥 USERS:\n{text}")

# ===================== MAIN CHAT =====================

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):

    uid = update.effective_user.id
    users.add(uid)
    init_user(uid)

    text = update.message.text

    # ================= GOALS =================
    if "help me" in text or "want to" in text:
        add_goal(uid, text)

    # ================= INTELLIGENCE =================

    context_input = intelligence_layer(uid, text)
    response = ai(context_input, uid)

    # ================= TASK SYSTEM =================

    if response.startswith("TASK:"):
        task = response.replace("TASK:", "").strip()
        add_task(uid, task)
        add_memory(uid, text)
        return await update.message.reply_text(f"📌 TASK:\n{task}")

    # ================= PLAN SYSTEM =================

    if response.startswith("PLAN:"):
        plan = response.replace("PLAN:", "").strip()
        add_memory(uid, text)
        return await update.message.reply_text(f"🧠 PLAN:\n{plan}")

    # ================= CONTINUATION =================

    if "continue" in text.lower():
        response = ai("Continue previous reasoning in deeper detail.", uid)

    add_memory(uid, text)
    await update.message.reply_text(response)

# ===================== RUN =====================

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN missing")

app = ApplicationBuilder().token(BOT_TOKEN).build()

# CORE COMMANDS
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("admin", admin))
app.add_handler(CommandHandler("stats", stats))
app.add_handler(CommandHandler("users", list_users))

# CHAT ENGINE
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

print("🤖 AUTONOMOUS AI AGENT v10 WITH ADMIN RUNNING...")
app.run_polling()
