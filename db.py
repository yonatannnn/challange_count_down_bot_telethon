from pymongo import MongoClient
from datetime import datetime, timedelta, timezone
import os
from dotenv import load_dotenv

load_dotenv()

client = MongoClient(os.getenv("MONGO_URI"))
db = client.daily_bot
challenges = db.challenges

def add_challenge(user_id, title, duration):
    now = datetime.now(timezone.utc)
    challenges.insert_one({
        "user_id": user_id,
        "title": title,
        "start_date": now,
        "duration": duration,
        "end_date": now + timedelta(days=duration)
    })

def get_active_challenges():
    now = datetime.now(timezone.utc)
    return challenges.find({"end_date": {"$gte": now}})

def get_user_challenges(user_id):
    now = datetime.now(timezone.utc)
    return challenges.find({"user_id": user_id, "end_date": {"$gte": now}})

def get_user_challenges(user_id):
    now = datetime.now(timezone.utc)
    return list(challenges.find({"user_id": user_id, "end_date": {"$gte": now}}))

def delete_challenge_by_id(challenge_id):
    from bson import ObjectId
    return challenges.delete_one({"_id": ObjectId(challenge_id)})

