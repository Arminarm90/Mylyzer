# user_manager.py
import json
import os

# Path to the JSON file where user Telegram ID to phone number mappings are stored 📍
USER_DATA_FILE = "user_data/users.json"

def get_chat_id(user_id):
    path = f"user_data/{user_id}/chat_id.txt"
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return int(f.read().strip())
        except Exception as e:
            print(f"⚠️ خطا در خواندن chat_id کاربر {user_id}: {e}")
            return None
    return None

def load_user_data():
    """
    Loads user data (Telegram ID to phone number mapping) from a JSON file. 📥
    Returns an empty dictionary if the file does not exist. 📁
    """
    if os.path.exists(USER_DATA_FILE):
        try:
            with open(USER_DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print(f"Error decoding JSON from {USER_DATA_FILE}. Returning empty data. ❌")
            return {}
    return {}

def save_user_data(user_data):
    """
    Saves user data (Telegram ID to phone number mapping) to a JSON file. 💾
    Ensures the directory exists before saving. ✅
    """
    os.makedirs(os.path.dirname(USER_DATA_FILE), exist_ok=True)
    try:
        with open(USER_DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(user_data, f, indent=4, ensure_ascii=False) # ensure_ascii=False for Persian characters ✍️
    except IOError as e:
        print(f"Error saving user data to {USER_DATA_FILE}: {e} 🚫")

def get_user_phone(telegram_user_id):
    """
    Retrieves the phone number associated with a given Telegram user ID. 📞
    Returns None if the user ID is not found. 🤷‍♂️
    """
    user_data = load_user_data()
    # Convert telegram_user_id to string as JSON keys are strings ➡️
    return user_data.get(str(telegram_user_id))

def save_user_phone(telegram_user_id, phone_number):
    """
    Saves or updates the phone number for a given Telegram user ID. ➕
    """
    user_data = load_user_data()
    user_data[str(telegram_user_id)] = phone_number
    save_user_data(user_data)
    print(f"Phone number {phone_number} saved for user {telegram_user_id} ✅")

# User logs for notifs
import os
import json
from datetime import datetime

def get_notifications_log(user_id):
    folder = f"user_data/{user_id}"
    path = f"{folder}/notifications_log.json"

    # ساخت پوشه اگر وجود نداشت
    os.makedirs(folder, exist_ok=True)

    # اگر فایل وجود نداشت، لاگ خالی برگردون
    if not os.path.exists(path):
        return []

    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_notification(user_id, customer_id, notif_type):
    path = f"user_data/{user_id}/notifications_log.json"
    os.makedirs(os.path.dirname(path), exist_ok=True)

    logs = []
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            try:
                logs = json.load(f)
            except json.JSONDecodeError:
                logs = []

    logs.append({
        "customer_id": customer_id,
        "notif_type": notif_type,
        "sent_at": datetime.now().isoformat(timespec='minutes'),
        "seen": False
    })

    with open(path, 'w', encoding='utf-8') as f:
        json.dump(logs, f, ensure_ascii=False, indent=2)


def has_notification_been_sent(user_id, customer_id, notif_type, cooldown_days=0):
    path = f"user_data/{user_id}/notifications_log.json"
    if not os.path.exists(path):
        return False

    with open(path, 'r', encoding='utf-8') as f:
        try:
            logs = json.load(f)
        except json.JSONDecodeError:
            return False

    now = datetime.now()
    for log in logs:
        if (
            log['customer_id'] == customer_id and
            log['notif_type'] == notif_type
        ):
            if cooldown_days > 0:
                try:
                    sent_time = datetime.fromisoformat(log['sent_at'])
                    if (now - sent_time).days < cooldown_days:
                        return True
                except:
                    continue
            else:
                return True
    return False

