import asyncio
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timezone
from db import get_active_challenges
from telethon.sync import TelegramClient
import os
from dotenv import load_dotenv
from collections import defaultdict
from telethon.sessions import StringSession

load_dotenv()

client = TelegramClient(StringSession(), int(os.getenv("API_ID")), os.getenv("API_HASH")).start(bot_token=os.getenv("BOT_TOKEN"))

import asyncio

async def send_daily_updates():
    print("Running daily update...")
    now = datetime.now(timezone.utc)
    challenges_by_user = defaultdict(list)

    for challenge in get_active_challenges():
        end_date = challenge.get('end_date')
        if end_date.tzinfo is None:
            end_date = end_date.replace(tzinfo=timezone.utc)

        days_left = (end_date - now).days
        if days_left < 0:
            continue

        msg = f"- {days_left} day{'s' if days_left != 1 else ''} left for: \"{challenge['title']}\""
        challenges_by_user[challenge['user_id']].append(msg)

    for user_id, messages in challenges_by_user.items():
        text = "🌞 Good morning! Here's your challenge update:\n\n" + "\n".join(messages)
        try:
            await client.send_message(user_id, text)
        except Exception as e:
            print(f"❌ Failed to send to {user_id}: {e}")



def start_scheduler(loop):
    scheduler = BackgroundScheduler(timezone="Africa/Addis_Ababa")

    def scheduled_wrapper():
        asyncio.run_coroutine_threadsafe(send_daily_updates(), loop)

    scheduler.add_job(scheduled_wrapper, 'cron', hour=6, minute=0)
    scheduler.start()

