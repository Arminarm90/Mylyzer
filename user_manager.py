# user_manager.py
import json
import os
import logging
from datetime import datetime # Import datetime for date comparisons
import jdatetime # Import jdatetime for Shamsi date conversion

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Path to the JSON file where user Telegram ID, phone number, and chat ID mappings are stored 📍
USER_DATA_FILE = "user_data/users.json"
# Directory to store user-specific notification logs and other data
DATA_DIR = "user_data" # Ensure this is defined

def load_user_data():
    """
    Loads user data (Telegram ID to phone number and chat ID mapping) from a JSON file. 📥
    Returns an empty dictionary if the file does not exist or is malformed. 📁
    """
    if os.path.exists(USER_DATA_FILE):
        try:
            with open(USER_DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Ensure the loaded data is actually a dictionary
                if not isinstance(data, dict):
                    logger.error(f"Root of {USER_DATA_FILE} is not a dictionary (it's type: {type(data)}). Returning empty data. ❌")
                    return {}
                # logger.info(f"Successfully loaded user data from {USER_DATA_FILE}. Keys: {list(data.keys())[:5]}...")
                return data
        except json.JSONDecodeError:
            logger.error(f"Error decoding JSON from {USER_DATA_FILE}. Returning empty data. ❌")
            return {}
    logger.info(f"User data file not found at {USER_DATA_FILE}. Returning empty dictionary.")
    return {}

def save_user_data(user_data):
    """
    Saves user data to a JSON file. 💾
    Ensures the directory exists before saving. ✅
    """
    os.makedirs(os.path.dirname(USER_DATA_FILE), exist_ok=True)
    try:
        with open(USER_DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(user_data, f, indent=4, ensure_ascii=False) # ensure_ascii=False for Persian characters ✍️
            # logger.info(f"User data saved successfully to {USER_DATA_FILE}. Keys saved: {list(user_data.keys())[:5]}...")
    except IOError as e:
        logger.error(f"Error saving user data to {USER_DATA_FILE}: {e} 🚫")

def get_user_phone(telegram_user_id):
    """
    Retrieves the phone number associated with a given Telegram user ID. 📞
    Returns None if the user ID is not found. 🤷‍♂️
    This function handles both new (dictionary) and old (string) formats of user data.
    """
    user_data = load_user_data()
    user_id_str = str(telegram_user_id)
    user_info = user_data.get(user_id_str)
    
    if user_info:
        if isinstance(user_info, dict):
            # New format: user_info is a dictionary
            return user_info.get('phone_number')
        elif isinstance(user_info, str):
            # Old format: user_info is a direct string (the phone number)
            logger.warning(f"Old user data format detected for user {user_id_str}. Phone number is a direct string.")
            return user_info # Return the phone number if it's a direct string
    
    logger.info(f"Phone number not found or invalid format for user {user_id_str}.")
    return None

def get_chat_id(telegram_user_id):
    """
    Retrieves the chat ID associated with a given Telegram user ID. 💬
    Returns None if the user ID or chat ID is not found. 🤷‍♂️
    If the user data is in the old string format, it assumes chat_id is the user_id.
    """
    user_data = load_user_data()
    user_id_str = str(telegram_user_id)
    user_info = user_data.get(user_id_str)

    logger.info(f"Attempting to get chat_id for user {user_id_str}. user_info type: {type(user_info)}, value: {user_info}")

    # If user_info is a dictionary (new format)
    if user_info and isinstance(user_info, dict):
        chat_id = user_info.get('chat_id')
        if chat_id:
            logger.info(f"Chat ID {chat_id} found for user {user_id_str}.")
            return chat_id
        else:
            logger.warning(f"Chat ID key missing for user {user_id_str} in user_data (new format).")
            # If chat_id is missing in new format, try to fallback to user_id (common for private chats)
            return telegram_user_id # Fallback to user_id as chat_id if not explicitly present
    # If user_info is a string (old format)
    elif isinstance(user_info, str): 
        logger.warning(f"User data for {user_id_str} is in old string format (type: {type(user_info)}). Assuming chat_id is user_id.")
        return telegram_user_id # In old format, chat_id often defaults to user_id in private chats
    
    logger.warning(f"User {user_id_str} not found in user data.")
    return None

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
    

def has_notification_been_sent(user_id, customer_id, notif_type, cooldown_days=0):
    """
    Checks if a specific notification has been sent for a customer within a cooldown period.
    Saves and loads notification log from a JSON file.
    """
    log_file_path = os.path.join(DATA_DIR, str(user_id), "notification_log.json")
    
    log_data = {}
    if os.path.exists(log_file_path):
        try:
            with open(log_file_path, 'r', encoding='utf-8') as f:
                log_data = json.load(f)
        except json.JSONDecodeError:
            logger.error(f"Error decoding notification log JSON from {log_file_path}. Starting fresh.")
            log_data = {}

    key = f"{customer_id}_{notif_type}"
    if key in log_data:
        last_sent_str = log_data[key]
        try:
            last_sent_date = datetime.strptime(last_sent_str, "%Y-%m-%d")
            # Get current Gregorian date
            current_greg_date = jdatetime.date.today().togregorian()
            current_date = datetime(current_greg_date.year, current_greg_date.month, current_greg_date.day)
            
            if (current_date - last_sent_date).days < cooldown_days:
                logger.info(f"Notification '{notif_type}' for customer '{customer_id}' by user '{user_id}' is still in cooldown.")
                return True
        except ValueError:
            logger.warning(f"Invalid date format in notification log for key {key}: {last_sent_str}. Treating as never sent.")
            return False # Treat as never sent if date format is invalid
    return False

def save_notification(user_id, customer_id, notif_type):
    """
    Logs that a specific notification has been sent for a customer.
    """
    user_dir = os.path.join(DATA_DIR, str(user_id))
    os.makedirs(user_dir, exist_ok=True)
    log_file_path = os.path.join(user_dir, "notification_log.json")

    log_data = {}
    if os.path.exists(log_file_path):
        try:
            with open(log_file_path, 'r', encoding='utf-8') as f:
                log_data = json.load(f)
        except json.JSONDecodeError:
            logger.error(f"Error decoding notification log JSON from {log_file_path}. Overwriting.")
            log_data = {}
            
    key = f"{customer_id}_{notif_type}"
    # Get current Gregorian date for logging
    current_greg_date = jdatetime.date.today().togregorian()
    log_data[key] = current_greg_date.strftime("%Y-%m-%d")

    try:
        with open(log_file_path, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, indent=4, ensure_ascii=False)
        logger.info(f"Notification '{notif_type}' for customer '{customer_id}' by user '{user_id}' logged successfully.")
    except IOError as e:
        logger.error(f"Error saving notification log to {log_file_path}: {e}")

