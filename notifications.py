# Import custom modules 📚
from user_manager import save_notification, has_notification_been_sent
from data_analyzer import get_full_customer_segments_df
from user_manager import has_notification_been_sent, save_notification
import os
import pandas as pd


# Directory to store user-specific Excel files and user data JSON 📁
DATA_DIR = "user_data"

# Ensure data directory exists ✨
os.makedirs(DATA_DIR, exist_ok=True)


def load_data_from_excel(excel_path):
    df_customers = pd.read_excel(excel_path, sheet_name="Customers")
    df_transactions = pd.read_excel(excel_path, sheet_name="Transactions")
    return df_customers, df_transactions


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


# In Danger Users
async def check_and_notify_at_risk_customers(user_id, context, chat_id):
    file_path = get_user_excel_path(user_id)
    if not os.path.exists(file_path):
        return

    df_customers, df_transactions = load_data_from_excel(file_path)
    if df_customers.empty or df_transactions.empty:
        return

    from data_analyzer import get_full_customer_segments_df  # حتماً ایمپورت باشه

    df_segmented = get_full_customer_segments_df(df_transactions, df_customers)
    at_risk_customers = df_segmented[
        (df_segmented["دسته رفتاری نهایی"] == "در خطر")
        & (df_segmented["روز از آخرین خرید"] >= 15)
        & (df_segmented["روز از آخرین خرید"] <= 30)
    ]

    for _, row in at_risk_customers.iterrows():
        customer_id = row["کد مشتری"]
        customer_name = row["نام مشتری"]

        if not has_notification_been_sent(
            user_id, customer_id, "AT_RISK", cooldown_days=15
        ):
            message = (
                f"⚠️ مشتری {customer_name} اخیراً خرید نکرده و وارد دسته در خطر شده.\n"
                f"با یه یادآوری یا پیشنهاد محدود برش گردون. 💬"
            )
            await context.bot.send_message(chat_id=chat_id, text=message)
            save_notification(user_id, customer_id, "AT_RISK")


async def check_and_notify_at_risk_customers_for_all_users(context):
    def get_all_user_ids():
        user_data_dir = "user_data"
        return [
            os.path.splitext(f)[0] for f in os.listdir(user_data_dir)
            if f.endswith(".xlsx")
        ]
        
    user_ids = get_all_user_ids()
    for user_id in user_ids:
        # اگر chat_id رو ذخیره می‌کنی، اینجا بگیر. اگر نه دستی بده یا از فایل بخون
        chat_id = int(user_id)  # فرض می‌کنیم برابر با user_id
        try:
            await check_and_notify_at_risk_customers(user_id, context, chat_id)
        except Exception as e:
            print(f"❌ خطا برای کاربر {user_id}: {e}")
