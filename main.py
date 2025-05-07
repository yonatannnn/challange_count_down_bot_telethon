import asyncio
from telethon import TelegramClient, events, Button
import os
from dotenv import load_dotenv
from db import add_challenge
from scheduler import start_scheduler
from db import get_user_challenges, delete_challenge_by_id
from telethon import Button
from telethon.sessions import StringSession

load_dotenv()

# Track pending delete requests: user_id → { challenge_id → title }
pending_deletes = {}

api_id = int(os.getenv("API_ID"))
api_hash = os.getenv("API_HASH")
bot_token = os.getenv("BOT_TOKEN")

os.makedirs("sessions", exist_ok=True)
bot = TelegramClient(StringSession(), api_id, api_hash).start(bot_token=bot_token)

@bot.on(events.NewMessage(pattern='/start'))
async def start(event):
    await event.respond("👋 Welcome! Use /add_challenge to begin a countdown challenge.")

@bot.on(events.NewMessage(pattern='/add_challenge'))
async def add_challenge_handler(event):
    sender = await event.get_sender()
    user_id = sender.id

    async with bot.conversation(user_id, timeout=120) as conv:
        await conv.send_message("📝 Please enter the *title* of your challenge:", parse_mode='md')
        title_msg = await conv.get_response()
        title = title_msg.text.strip()
        await conv.send_message("📅 Enter the *duration* in days (e.g., 30):", parse_mode='md')
        duration_msg = await conv.get_response()
        try:
            duration = int(duration_msg.text.strip())
            if duration <= 0:
                raise ValueError()
        except ValueError:
            await conv.send_message("❌ Invalid duration. Please try `/add_challenge` again.")
            return

        add_challenge(user_id, title, duration)
        await conv.send_message(f"✅ Challenge *'{title}'* added for {duration} days!", parse_mode='md')

@bot.on(events.NewMessage(pattern='/delete_challenge'))
async def delete_challenge_handler(event):
    sender = await event.get_sender()
    user_id = sender.id

    user_challenges = get_user_challenges(user_id)
    if not user_challenges:
        await event.respond("🫤 You have no active challenges to delete.")
        return

    buttons = []
    challenge_map = {}
    for i, ch in enumerate(user_challenges, 1):
        label = f"{i}. {ch['title']}"
        challenge_id = str(ch['_id'])
        buttons.append([Button.inline(label, data=challenge_id.encode())])
        challenge_map[challenge_id] = ch['title']

    pending_deletes[user_id] = challenge_map  # track choices
    await event.respond("🗑 Select a challenge to cancel:", buttons=buttons)

@bot.on(events.CallbackQuery)
async def handle_delete_click(event):
    user_id = event.sender_id
    challenge_id = event.data.decode()

    if user_id not in pending_deletes:
        await event.answer("⚠️ No deletion request found.")
        return

    if challenge_id not in pending_deletes[user_id]:
        await event.answer("⚠️ Invalid selection.")
        return

    title = pending_deletes[user_id].pop(challenge_id)
    delete_challenge_by_id(challenge_id)
    await event.answer()
    await event.respond(f"✅ Challenge *'{title}'* has been cancelled.", parse_mode='md')

    # Clean up if empty
    if not pending_deletes[user_id]:
        del pending_deletes[user_id]




start_scheduler(bot.loop)
print("Bot is running...")
bot.run_until_disconnected()
