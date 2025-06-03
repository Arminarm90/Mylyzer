# user_manager.py
import json
import os

# Path to the JSON file where user Telegram ID to phone number mappings are stored 📍
USER_DATA_FILE = "user_data/users.json"

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

