# notifications.py
import os
import pandas as pd
import logging
from datetime import datetime # For date comparisons in cooldown logic
import jdatetime # For converting jdatetime.date to Gregorian datetime object

# Import custom modules 📚
from user_manager import has_notification_been_sent, save_notification, get_chat_id, load_user_data # Import get_chat_id
from data_analyzer import get_full_customer_segments_df
from dotenv import load_dotenv
import requests

load_dotenv()

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Directory to store user-specific Excel files and user data JSON 📁
DATA_DIR = "user_data"
BOT_TOKEN = os.getenv("BOT_TOKEN")
# Ensure data directory exists ✨
os.makedirs(DATA_DIR, exist_ok=True)


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


# VIP Users
async def check_and_notify_vip_after_purchase(user_id, context, chat_id):
    print("✅ check_and_notify_vip_after_purchase CALLED")

    file_path = get_user_excel_path(user_id)

    if not os.path.exists(file_path):
        return
    print("✅ فایل اکسل پیدا شد:", file_path)

    df_customers, df_transactions = load_data_from_excel(file_path)
    if df_customers.empty or df_transactions.empty:
        print("⚠️ یکی از دیتافریم‌ها خالیه")

        return

    df_segmented = get_full_customer_segments_df(df_transactions, df_customers)
    vip_customers = df_segmented[df_segmented["دسته رفتاری نهایی"] == "ویژه"]

    for _, row in vip_customers.iterrows():
        customer_id = row["کد مشتری"]
        customer_name = row["نام مشتری"]

        if not has_notification_been_sent(user_id, customer_id, "VIP"):
            notif_text = (
                f"🎯 مشتری ویژه شناسایی شد!\n"
                f"{customer_name} به دسته VIP ارتقاء یافته است.\n"
                f"مراقب این مشتریان با ارزش باشید! 💎"
            )
            await context.bot.send_message(chat_id=chat_id, text=notif_text)
            save_notification(user_id, customer_id, "VIP")


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

        vip_customers = df_segmented[df_segmented["دسته رفتاری نهایی"] == "ویژه"]

        if vip_customers.empty:
            logger.info(f"User {user_id}: Found 0 VIP customers.")
            return

        logger.info(f"User {user_id}: Found {len(vip_customers)} VIP customers.")

        for _, row in vip_customers.iterrows():
            customer_id = row["کد مشتری"]
            customer_name = row["نام مشتری"]

            # Check if notification has been sent for this VIP customer within a reasonable cooldown (e.g., 90 days)
            if not has_notification_been_sent(
                user_id, customer_id, "VIP", cooldown_days=90
            ):
                message = (
                    f"🎉 مشتری {customer_name} در دسته ویژه قرار گرفت!"
                    f" وقتشه با یه پاداش اختصاصی یا تخفیف خاص بهش وفاداری نشون بدی. 💎"
                )
                # Use the direct send_telegram_message function
                if send_telegram_message(chat_id, message):
                    save_notification(user_id, customer_id, "VIP")
                else:
                    logger.error(f"Failed to send VIP notification to {chat_id} for user {user_id}, customer {customer_id}.")
            else:
                logger.info(f"VIP notification for customer {customer_id} (user {user_id}) already sent or in cooldown.")
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

        # Ensure 'روز از آخرین خرید' is numeric for comparison (though not directly used in the final filter below)
        df_segmented['روز از آخرین خرید'] = pd.to_numeric(df_segmented['روز از آخرین خرید'], errors='coerce')
        df_segmented.dropna(subset=["روز از آخرین خرید"], inplace=True) # Drop any rows where conversion failed


        # Rely only on the 'دسته رفتاری نهایی' (segment label) and the recency condition implied by TAM 'At Risk'
        # The 'در خطر' segment definition uses TAM='At Risk', which in turn means Recency <= 90.
        # However, the user's previous code had a specific range of 15-30 days. 
        # Re-introducing a filter for a *subset* of 'در خطر' if that's the desired notification trigger,
        # but making it align with the 'At Risk' TAM definition (31-90 days).
        at_risk_customers = df_segmented[
            (df_segmented["دسته رفتاری نهایی"] == "در خطر")
            # If the user specifically wants to notify AT_RISK customers
            # who are *also* in a certain recency window, this filter is necessary.
            # Assuming "در خطر" implies TAM_Status "At Risk" (31-90 days)
            # and the user wants to notify those who are in the deeper part of that risk.
            # Let's use 31-90 days as the range for notifications, consistent with TAM.
            & (df_segmented["روز از آخرین خرید"] > 30)  # Starts after active period
            & (df_segmented["روز از آخرین خرید"] <= 90) # Within the at-risk TAM period
        ]

        if at_risk_customers.empty:
            logger.info(f"User {user_id}: Found 0 at-risk customers meeting criteria (Recency 31-90 days).")
            return

        logger.info(f"User {user_id}: Found {len(at_risk_customers)} at-risk customers meeting criteria (Recency 31-90 days).")

        for _, row in at_risk_customers.iterrows():
            customer_id = row["کد مشتری"]
            customer_name = row["نام مشتری"]

            # Cooldown of 15 days is defined in user_manager.py for AT_RISK notifications
            if not has_notification_been_sent(
                user_id, customer_id, "AT_RISK", cooldown_days=15 
            ):
                message = (
                    f"⚠️ مشتری '{customer_name}' با کد '{customer_id}' اخیراً خرید نکرده و وارد دسته در خطر شده.\\n"
                    f"با یه یادآوری یا پیشنهاد محدود برش گردون. 💬"
                )
                # Use the direct send_telegram_message function
                if send_telegram_message(chat_id, message):
                    save_notification(user_id, customer_id, "AT_RISK")
                else:
                    logger.error(f"Failed to send At-Risk notification to {chat_id} for user {user_id}, customer {customer_id}.")
            else:
                logger.info(f"AT_RISK notification for customer {customer_id} (user {user_id}) already sent or in cooldown.")
    except Exception as e:
        logger.error(f"Error during At-Risk notification check for user {user_id}: {e}")


async def check_and_notify_at_risk_customers_for_all_users(context):
    """
    Iterates through all users and triggers the 'At Risk' customer notification check.
    This function is intended to be run by the scheduler.
    """
    logger.info("Starting scheduled check for at-risk customers for all users. ⏰")

    # Assuming load_user_data is accessible (it's in user_manager, which is imported)
    from user_manager import load_user_data 
    all_user_data = load_user_data() 
    
    # Filter for user_ids that have entries in user_data
    # Convert keys to int as user_id is expected to be int
    user_ids = [int(uid) for uid in all_user_data.keys() if all_user_data.get(uid)] 

    if not user_ids:
        logger.info("No active users found in user_data. Skipping scheduled at-risk check.")
        return
        
    for user_id in user_ids:
        try:
            # Retrieve chat_id from user_manager.py using the user_id
            chat_id = get_chat_id(user_id) 
            
            if chat_id:
                logger.info(f"Processing user {user_id} (chat_id: {chat_id}) for at-risk notifications.")
                # Pass the original context object for now, as it still has the bot instance from main.py's Application
                # However, the send_telegram_message function will use direct requests
                await check_and_notify_at_risk_customers(user_id, context, chat_id)
            else:
                logger.warning(f"❌ Could not find chat_id for user {user_id}. Skipping at-risk notification for this user.")
        except Exception as e:
            logger.error(f"An error occurred during at-risk check for user {user_id}: {e}")