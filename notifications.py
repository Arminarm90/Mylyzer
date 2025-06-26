# notifications.py
import os
import pandas as pd
import logging
from datetime import datetime # For date comparisons in cooldown logic
import jdatetime # For converting jdatetime.date to Gregorian datetime object
import requests # Import requests for direct API calls 
from dotenv import load_dotenv # Import load_dotenv

load_dotenv() # Load environment variables

# Import custom modules 📚
from user_manager import has_notification_been_sent, save_notification, get_chat_id, load_user_data
from data_analyzer import get_full_customer_segments_df

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Directory to store user-specific Excel files and user data JSON 📁
DATA_DIR = "user_data"

# Ensure data directory exists ✨
os.makedirs(DATA_DIR, exist_ok=True)

# Get BOT_TOKEN from environment variables 
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    logger.error("BOT_TOKEN environment variable not set. Notifications will not be sent.")


def load_data_from_excel(excel_path):
    """Loads customer and transaction data from a user's Excel file."""
    try:
        df_customers = pd.read_excel(excel_path, sheet_name="Customers")
        df_transactions = pd.read_excel(excel_path, sheet_name="Transactions")
        return df_customers, df_transactions
    except FileNotFoundError:
        logger.warning(f"Excel file not found at {excel_path}. Returning empty DataFrames.")
        return pd.DataFrame(), pd.DataFrame()
    except Exception as e:
        logger.error(f"Error loading data from Excel file {excel_path}: {e}")
        return pd.DataFrame(), pd.DataFrame()


# --- Helper Functions 🛠️ ---
def get_user_excel_path(user_id):
    """
    Returns the path to the user's dedicated Excel file. 📄
    Each user gets a unique Excel file based on their Telegram user ID.
    """
    return os.path.join(DATA_DIR, f"{user_id}.xlsx")


def send_telegram_message(chat_id, text):
    """
    Sends a message to a specific chat ID using the Telegram Bot API (direct HTTP request).
    """
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN is not set. Cannot send messages.")
        return False

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML" # Use HTML for basic formatting if needed
    }
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
        logger.info(f"Message sent successfully to chat_id {chat_id}.")
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to send message to chat_id {chat_id}: {e}")
        return False


# VIP Users
async def check_and_notify_vip_after_purchase(user_id, context, chat_id):
    logger.info(f"✅ check_and_notify_vip_after_purchase CALLED for user {user_id}")

    file_path = get_user_excel_path(user_id)

    if not os.path.exists(file_path):
        logger.warning(f"Excel file for user {user_id} not found at {file_path}. Skipping VIP check.")
        return

    df_customers, df_transactions = load_data_from_excel(file_path)

    if df_transactions.empty or df_customers.empty:
        logger.info(f"User {user_id}: No customer or transaction data available for VIP check.")
        return
    
    # Needs enough transactions for meaningful analysis (e.g., at least 5 for KMeans to work well)
    if len(df_transactions) < 5:
        logger.info(f"VIP check: Not enough transactions ({len(df_transactions)}) for user {user_id} for meaningful analysis. Skipping notification.")
        return

    try:
        df_segmented = get_full_customer_segments_df(df_transactions, df_customers)

        if df_segmented.empty:
            logger.info(f"User {user_id}: No segmented data available for VIP check.")
            return

        vip_customers_to_notify = []
        vip_customers = df_segmented[df_segmented["دسته رفتاری نهایی"] == "ویژه"]

        for _, row in vip_customers.iterrows():
            customer_id = row["کد مشتری"]
            customer_name = row["نام مشتری"]

            if not has_notification_been_sent(
                user_id, customer_id, "VIP", cooldown_days=90 # Cooldown for VIP is 90 days
            ):
                vip_customers_to_notify.append(f"- {customer_name} (کد: {customer_id})")
                save_notification(user_id, customer_id, "VIP") # Log immediately after deciding to notify

        if vip_customers_to_notify:
            message_body = "\n".join(vip_customers_to_notify)
            message = (
                f"🎯 مشتریان ویژه جدید شناسایی شدند!\n"
                f"لیست مشتریانی که به دسته VIP ارتقاء یافته‌اند:\n"
                f"{message_body}\n"
                f"مراقب این مشتریان با ارزش باشید! 💎"
            )
            if send_telegram_message(chat_id, message):
                logger.info(f"Consolidated VIP notification sent to {chat_id} for user {user_id}.")
            else:
                logger.error(f"Failed to send consolidated VIP notification to {chat_id} for user {user_id}.")
        else:
            logger.info(f"User {user_id}: No new VIP customers to notify after considering cooldown.")

    except Exception as e:
        logger.error(f"Error during VIP notification check for user {user_id}: {e}")

# At-Risk Users
async def check_and_notify_at_risk_customers(user_id, context, chat_id):
    logger.info(f"⚠️ check_and_notify_at_risk_customers CALLED for user {user_id}")

    file_path = get_user_excel_path(user_id)
    if not os.path.exists(file_path):
        logger.warning(f"Excel file for user {user_id} not found at {file_path}. Skipping at-risk check.")
        return

    df_customers, df_transactions = load_data_from_excel(file_path)

    if df_transactions.empty or df_customers.empty:
        logger.info(f"User {user_id}: No customer or transaction data available for at-risk check.")
        return

    # Needs enough transactions for meaningful analysis (e.g., at least 5 for KMeans to work well)
    if len(df_transactions) < 5:
        logger.info(f"At-Risk check: Not enough transactions ({len(df_transactions)}) for user {user_id} for meaningful analysis. Skipping notification.")
        return

    try:
        df_segmented = get_full_customer_segments_df(df_transactions, df_customers) 

        if df_segmented.empty:
            logger.info(f"User {user_id}: No segmented data available for at-risk check.")
            return

        df_segmented['روز از آخرین خرید'] = pd.to_numeric(df_segmented['روز از آخرین خرید'], errors='coerce')
        df_segmented.dropna(subset=["روز از آخرین خرید"], inplace=True) 

        at_risk_customers_to_notify = []
        at_risk_customers = df_segmented[
            (df_segmented["دسته رفتاری نهایی"] == "در خطر")
            & (df_segmented["روز از آخرین خرید"] > 30)  # Starts after active period
            & (df_segmented["روز از آخرین خرید"] <= 90) # Within the at-risk TAM period (31-90 days)
        ]

        if at_risk_customers.empty:
            logger.info(f"User {user_id}: Found 0 at-risk customers meeting criteria (Recency 31-90 days).")
            return

        logger.info(f"User {user_id}: Found {len(at_risk_customers)} at-risk customers meeting criteria (Recency 31-90 days).")

        for _, row in at_risk_customers.iterrows():
            customer_id = row["کد مشتری"]
            customer_name = row["نام مشتری"]

            if not has_notification_been_sent(
                user_id, customer_id, "AT_RISK", cooldown_days=15 # Cooldown for At-Risk is 15 days
            ):
                at_risk_customers_to_notify.append(f"- {customer_name} (کد: {customer_id})")
                save_notification(user_id, customer_id, "AT_RISK") # Log immediately after deciding to notify

        if at_risk_customers_to_notify:
            message_body = "\n".join(at_risk_customers_to_notify)
            message = (
                f"⚠️ مشتریان در خطر جدید شناسایی شدند!\n"
                f"لیست مشتریانی که اخیراً خرید نکرده و وارد دسته در خطر شده‌اند:\n"
                f"{message_body}\n"
                f"با یه یادآوری یا پیشنهاد محدود برش گردون. 💬"
            )
            if send_telegram_message(chat_id, message):
                logger.info(f"Consolidated At-Risk notification sent to {chat_id} for user {user_id}.")
            else:
                logger.error(f"Failed to send consolidated At-Risk notification to {chat_id} for user {user_id}.")
        else:
            logger.info(f"User {user_id}: No new At-Risk customers to notify after considering cooldown.")

    except Exception as e:
        logger.error(f"Error during At-Risk notification check for user {user_id}: {e}")


async def check_and_notify_at_risk_customers_for_all_users(context):
    """
    Iterates through all users and triggers the 'At Risk' customer notification check.
    This function is intended to be run by the scheduler.
    """
    logger.info("Starting scheduled check for at-risk customers for all users. ⏰")

    from user_manager import load_user_data 
    all_user_data = load_user_data() 
    
    user_ids = [int(uid) for uid in all_user_data.keys() if all_user_data.get(uid)] 

    if not user_ids:
        logger.info("No active users found in user_data. Skipping scheduled at-risk check.")
        return
        
    for user_id in user_ids:
        try:
            chat_id = get_chat_id(user_id) 
            
            if chat_id:
                logger.info(f"Processing user {user_id} (chat_id: {chat_id}) for at-risk notifications.")
                # We are passing the original context, though send_telegram_message won't use it.
                # This keeps the function signature consistent with other async Telegram functions.
                await check_and_notify_at_risk_customers(user_id, context, chat_id) 
            else:
                logger.warning(f"❌ Could not find chat_id for user {user_id}. Skipping at-risk notification for this user.")
        except Exception as e:
            logger.error(f"An error occurred during at-risk check for user {user_id}: {e}")

