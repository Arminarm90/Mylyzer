# main.py
import logging
import os
import zipfile  # Import zipfile module for creating zip archives 📚
from telegram import (
    Update,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    InputFile,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)  # Import Inline buttons
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
    CallbackQueryHandler,
)  # Import CallbackQueryHandler
from dotenv import load_dotenv
import pandas as pd  # Import pandas for DataFrame manipulation
import re

# Import custom modules 📚
import excel_manager
import user_manager
import data_analyzer
from user_manager import save_notification, has_notification_been_sent, get_chat_id

# charts
from chart_utils import create_rfm_pie_chart, create_tam_bar_chart
from data_analyzer import get_full_customer_segments_df

# scheduler
from scheduler import start_scheduler

# notifications
from notifications import check_and_notify_vip_after_purchase

# date
import datetime
import jdatetime

# load env
load_dotenv()


# Enable logging 📝
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Global Configurations ⚙️ ---
# Replace with your bot token obtained from BotFather 🤖
# For security, consider using environment variables for the bot token.
BOT_TOKEN = os.getenv("BOT_TOKEN")
# Directory to store user-specific Excel files and user data JSON 📁
DATA_DIR = "user_data"

# Ensure data directory exists ✨
os.makedirs(DATA_DIR, exist_ok=True)

# --- ConversationHandler States for /new_purchase 💬 ---
# New states for selecting entry mode and bulk data input
(
    SELECT_ENTRY_MODE,
    SINGLE_CUSTOMER_NAME,
    SINGLE_CUSTOMER_PHONE,
    SINGLE_PURCHASE_AMOUNT,
    BULK_PURCHASE_DATA,
) = range(5)
ANALYZE_DATA_ENTRY, SELECT_SEGMENT_TYPE = range(
    5, 7
)  # Start from 5 to avoid conflict with previous states


# --- Helper Functions 🛠️ ---
def get_user_excel_path(user_id):
    """
    Returns the path to the user's dedicated Excel file. 📄
    Each user gets a unique Excel file based on their Telegram user ID.
    """
    return os.path.join(DATA_DIR, f"{user_id}.xlsx")


async def send_file_to_user(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    file_path: str,
    caption: str = "",
):
    """
    Sends the specified file to the user. 📤
    Handles FileNotFoundError and other potential exceptions during file sending.
    """
    try:
        # Open the file in binary read mode and send it as a document 📂
        await update.message.reply_document(
            document=open(file_path, "rb"), caption=caption
        )
    except FileNotFoundError:
        logger.error(f"File not found at {file_path} ❌")
        await update.message.reply_text(
            "خطا: فایل یافت نشد. لطفاً دوباره تلاش کنید یا با پشتیبانی تماس بگیرید. 😟"
        )
    except Exception as e:
        logger.error(f"Error sending file: {e} 🚫")
        await update.message.reply_text("هنگام ارسال فایل خطایی رخ داد. 😔")


# --- Command Handlers 🚀 ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handles the /start command. 👋
    Welcomes the user and requests their phone number for authentication/identification.
    If the user's phone number is already registered, it shows the main commands.
    """
    user = update.effective_user
    logger.info(f"User {user.id} ({user.first_name}) started the bot. ▶️")

    # Get Chat ID
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    os.makedirs(f"user_data/{user_id}", exist_ok=True)
    with open(f"user_data/{user_id}/chat_id.txt", "w", encoding="utf-8") as f:
        f.write(str(chat_id))

    # Check if the user's phone number is already saved ✅
    if not user_manager.get_user_phone(user.id):
        # If not, request the phone number using a special keyboard button 📱
        keyboard = [[KeyboardButton("اشتراک گذاری شماره تماس", request_contact=True)]]
        reply_markup = ReplyKeyboardMarkup(
            keyboard, one_time_keyboard=True, resize_keyboard=True
        )
        await update.message.reply_text(
            f"سلام {user.first_name} عزیز! به ربات مدیریت خرید خوش آمدید. 👋\n"
            "لطفاً شماره تماس خود را به اشتراک بگذارید تا بتوانم داده‌های شما را مدیریت کنم. 🤝",
            reply_markup=reply_markup,
        )
    else:
        # If already registered, show the main menu 📋
        await update.message.reply_text(
            f"خوش آمدید {user.first_name}! 😊\n"
            "می‌توانید از دستورات زیر استفاده کنید:\n"
            "/new_purchase - ثبت خرید جدید 🛒\n"
            "/list_customers - لیست مشتریان 👥\n"
            "/list_transactions - تاریخچه تراکنش‌ها 💰\n"
            "/analyze_data - تحلیل رفتار مشتریان 📊\n",
            # "/get_full_excel - دریافت فایل اکسل کامل 📄\n",
            reply_markup=ReplyKeyboardRemove(),  # Remove the phone number sharing keyboard 🧹
        )


async def handle_contact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handles the shared phone number from the user. 📞
    Saves the phone number and initializes the user's Excel file if it doesn't exist.
    """
    user = update.effective_user
    contact = update.message.contact

    # Ensure the contact shared is the user's own contact 👍
    if contact and contact.user_id == user.id:
        phone_number = contact.phone_number
        user_manager.save_user_phone(user.id, phone_number)
        logger.info(
            f"User {user.id} ({user.first_name}) shared phone number: {phone_number} ✅"
        )

        excel_file_path = get_user_excel_path(user.id)
        # Create the initial Excel file if it does not exist for this user 🆕
        if not os.path.exists(excel_file_path):
            excel_manager.create_initial_excel(excel_file_path)
            await update.message.reply_text(
                f"فایل داده‌های شما ایجاد شد. آماده استفاده هستید! 🎉"
            )
        else:
            await update.message.reply_text("خوش آمدید! فایل داده‌های شما آماده است. 👍")

        # Display main commands after successful registration/login 🚀
        await update.message.reply_text(
            "اکنون می‌توانید از دستورات زیر استفاده کنید:\n"
            "/new_purchase - ثبت خرید جدید 🛒\n"
            "/list_customers - لیست مشتریان 👥\n"
            "/list_transactions - تاریخچه تراکنش‌ها 💰\n"
            "/analyze_data - تحلیل رفتار مشتریان 📊\n",
            # "/get_full_excel - دریافت فایل اکسل کامل 📄\n",
            reply_markup=ReplyKeyboardRemove(),  # Remove the phone number sharing keyboard 🧹
        )
    else:
        await update.message.reply_text(
            "لطفاً شماره تماس خودتان را به اشتراک بگذارید. ☝️"
        )


async def new_purchase_entry_point(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """
    Starts the conversation flow for registering a new purchase by asking the user for the entry mode. 📝
    """
    user_id = update.effective_user.id
    if not user_manager.get_user_phone(user_id):
        await update.message.reply_text(
            "لطفاً ابتدا با دستور /start شماره تماس خود را به اشتراک بگذارید. 📲"
        )
        return ConversationHandler.END  # End conversation if user is not registered 🛑

    keyboard = [
        [KeyboardButton("ثبت خرید تکی ➕")],
        [KeyboardButton("ثبت چند خرید (وزودی متنی) 📝")],
        [KeyboardButton("ثبت خرید با فایل اکسل 📄")],
        [KeyboardButton("خروج ⬅️")],
    ]
    reply_markup = ReplyKeyboardMarkup(
        keyboard, resize_keyboard=True, one_time_keyboard=True
    )
    await update.message.reply_text(
        "لطفاً نحوه ورود اطلاعات خرید را انتخاب کنید:", reply_markup=reply_markup
    )
    return SELECT_ENTRY_MODE  # Move to the state where user selects entry mode ➡️


async def select_single_entry(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """
    Triggered when user selects "ثبت خرید تکی ➕".
    Prompts for customer name and moves to SINGLE_CUSTOMER_NAME state.
    """
    await update.message.reply_text("لطفاً نام مشتری را وارد کنید: 🧑‍💼")
    return SINGLE_CUSTOMER_NAME


async def get_single_customer_name(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """
    Gets the customer's name for single entry and stores it in user_data. 💾
    Prompts for the customer's phone number next.
    """
    context.user_data["customer_name"] = update.message.text
    await update.message.reply_text("لطفاً شماره تلفن مشتری را وارد کنید: 📞")
    return SINGLE_CUSTOMER_PHONE  # Move to the next state to get customer phone ➡️


async def get_single_customer_phone(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """
    Gets the customer's phone number for single entry, performs basic validation, and stores it. ✅
    Prompts for the purchase amount next.
    """
    phone_number = update.message.text.strip()
    # Basic validation for phone number (e.g., only digits, minimum length) 🔢
    if not phone_number.isdigit() or len(phone_number) < 8:
        await update.message.reply_text(
            "شماره تلفن نامعتبر است. لطفاً یک شماره معتبر (فقط اعداد) وارد کنید: 🚫"
        )
        return SINGLE_CUSTOMER_PHONE  # Stay in the same state if validation fails 🔄

    context.user_data["customer_phone"] = phone_number
    await update.message.reply_text("لطفاً مبلغ خرید را (به تومان) وارد کنید: 💲")
    return SINGLE_PURCHASE_AMOUNT  # Move to the next state to get purchase amount ➡️


async def get_single_purchase_amount(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """
    Gets the purchase amount for single entry, performs validation, and saves the purchase. 💰
    Sends the updated Excel file to the user upon successful recording.
    """
    try:
        amount = int(update.message.text)
        if amount <= 0:
            raise ValueError  # Amount must be positive 📈
    except ValueError:
        await update.message.reply_text(
            "مبلغ نامعتبر است. لطفاً یک عدد مثبت وارد کنید: 🔢"
        )
        return SINGLE_PURCHASE_AMOUNT  # Stay in the same state if validation fails 🔄

    user_id = update.effective_user.id
    excel_file_path = get_user_excel_path(user_id)

    customer_name = context.user_data["customer_name"]
    customer_phone = context.user_data["customer_phone"]

    # Call excel_manager to save the purchase details ✍️
    excel_manager.save_purchase(excel_file_path, customer_name, customer_phone, amount)
    await check_and_notify_vip_after_purchase(
        user_id, context, update.effective_chat.id
    )
    await update.message.reply_text("خرید با موفقیت ثبت شد! 🎉")
    # await send_file_to_user(update, context, excel_file_path, caption="فایل اکسل به‌روز شده شما:") # Optional: Send the updated Excel file 📤
    return ConversationHandler.END  # End the conversation ✅


async def show_bulk_input_format(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """
    Shows user the required format for bulk input and moves to next state to receive the data.
    """
    await update.message.reply_text(
        "لطفاً اطلاعات مشتری‌ها را در قالب زیر وارد کنید (هر خط = یک مشتری):\n\n"
        "فرمت: نام و نام خانوادگی، شماره تلفن، مبلغ خرید\n"
        "مثال:\n"
        "علی رضایی،09351234567،150000\n"
        "نگار محمدی،09121234567،200000\n\n"
        "حالا لطفاً لیست مشتری‌ها را ارسال کنید:"
    )
    return BULK_PURCHASE_DATA


async def get_bulk_purchase_data(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """
    Processes multiple customer/purchase entries provided in a single text message.
    """
    user_id = update.effective_user.id
    excel_file_path = get_user_excel_path(user_id)
    raw_data_lines = update.message.text.strip().split("\n")

    successful_entries = 0
    failed_entries = []

    for line_num, line in enumerate(raw_data_lines, 1):
        line = line.strip()
        if not line:  # Skip empty lines
            continue

        parts = line.replace("،", ",").split(",")
        if (
            len(parts) < 3 or len(parts) > 4
        ):  # Expected: name, phone, description (optional), amount
            failed_entries.append(
                f"خط {line_num}: فرمت نامعتبر. باید حداقل شامل نام، شماره تلفن، مبلغ باشد. (مثال: نام،شماره،توضیحات،مبلغ)"
            )
            continue

        customer_name = parts[0].strip()
        customer_phone = parts[1].strip()
        description = (
            parts[2].strip() if len(parts) == 4 else ""
        )  # Description is optional
        amount_str = (
            parts[3].strip() if len(parts) == 4 else parts[2].strip()
        )  # Amount can be 3rd if no description

        # Basic validation for phone number and amount
        if not customer_phone.isdigit() or len(customer_phone) < 8:
            failed_entries.append(
                f"خط {line_num}: شماره تلفن '{customer_phone}' نامعتبر است."
            )
            continue

        try:
            amount = int(amount_str)
            if amount <= 0:
                raise ValueError
        except ValueError:
            failed_entries.append(
                f"خط {line_num}: مبلغ '{amount_str}' نامعتبر است. باید یک عدد مثبت باشد."
            )
            continue

        try:
            # Call excel_manager to save the customer and purchase details
            excel_manager.save_purchase_bulk(
                excel_file_path, customer_name, customer_phone, amount, description
            )  # Assuming description can be passed now
            successful_entries += 1
        except Exception as e:
            logger.error(f"Error saving bulk entry for line {line_num} ('{line}'): {e}")
            failed_entries.append(f"خط {line_num}: خطا در ذخیره اطلاعات ({e}).")

    response_message = f"عملیات ثبت چند خرید یکجا به پایان رسید. 🎉\n\n"
    response_message += f"تعداد ورودی‌های موفق: {successful_entries} ✅\n"

    if failed_entries:
        response_message += f"تعداد ورودی‌های ناموفق: {len(failed_entries)} ❌\n"
        response_message += "جزئیات خطاها:\n" + "\n".join(failed_entries)
    else:
        response_message += "همه ورودی‌ها با موفقیت ثبت شدند! 🥳"

    await update.message.reply_text(
        response_message, reply_markup=ReplyKeyboardRemove()
    )
    await check_and_notify_vip_after_purchase(
        user_id, context, update.effective_chat.id
    )

    # Optional: Send the updated Excel file after bulk processing
    # await send_file_to_user(update, context, excel_file_path, caption="فایل اکسل به‌روز شده شما:")
    return ConversationHandler.END  # End the conversation ✅


# Insert from excel file
WAITING_FOR_BULK_FILE = range(100, 101)  # حالت جدید


async def start_file_upload_flow(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    await update.message.reply_text(
        "برای ثبت چند خرید با فایل، لطفاً فایل اکسل را با فرمت زیر ارسال کنید:",
    )

    sample_path = "sample/bulk_purchase_template.xlsx"
    with open(sample_path, "rb") as f:
        await update.message.reply_document(
            InputFile(f), filename="نمونه-ثبت-خرید.xlsx"
        )

    return WAITING_FOR_BULK_FILE


async def handle_bulk_purchase_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Processes the uploaded Excel file for bulk purchase entries.
    """
    user_id = update.effective_user.id
    excel_path = get_user_excel_path(user_id)

    file = update.message.document
    if not file.file_name.endswith(".xlsx"):
        await update.message.reply_text(
            "⚠️ لطفاً فقط فایل اکسل با فرمت .xlsx ارسال کنید."
        )
        return ConversationHandler.END

    # Define a temporary path for the uploaded file specific to the user
    file_download_path = os.path.join(DATA_DIR, f"{user_id}_uploaded_bulk_purchase.xlsx")
    
    try:
        # Await the coroutine returned by get_file() before calling download_to_drive()
        await (await file.get_file()).download_to_drive(file_download_path)
        logger.info(f"User {user_id} uploaded bulk purchase file to: {file_download_path}")

        df = pd.read_excel(file_download_path)
        
        required_columns = {"نام مشتری", "شماره تماس", "مبلغ"}
        if not required_columns.issubset(set(df.columns)):
            await update.message.reply_text(
                "⚠️ ستون‌های مورد نیاز (`نام مشتری`, `شماره تماس`, `مبلغ`) در فایل اکسل پیدا نشدند. لطفاً طبق نمونه پر کنید."
            )
            os.remove(file_download_path) # Clean up the uploaded file
            return ConversationHandler.END

        success_count, fail_count = 0, 0
        processed_customer_phones = set() # To track which customers were processed for notifications

        for index, row in df.iterrows():
            try:
                name = str(row["نام مشتری"]).strip()
                phone = str(row["شماره تماس"]).strip()
                amount = int(row["مبلغ"])
                # 'توضیحات' column is optional, use .get() with a default empty string
                desc = str(row.get("توضیحات", "")).strip() 

                if not phone.isdigit() or len(phone) < 8:
                    raise ValueError(f"شماره تلفن '{phone}' نامعتبر است.")
                if amount <= 0:
                    raise ValueError(f"مبلغ '{amount}' نامعتبر است (باید مثبت باشد).")

                excel_manager.save_purchase_bulk(excel_path, name, phone, amount, desc)
                success_count += 1
                processed_customer_phones.add(phone) # Add phone to set for notification check
            except Exception as e:
                fail_count += 1
                logger.error(f"❌ خطا در ردیف {index + 1} فایل: {e}. ردیف: {row.to_dict()}")

        await update.message.reply_text(
            f"✅ عملیات ثبت فایل انجام شد.\nموفق: {success_count}\nناموفق: {fail_count}",
            reply_markup=ReplyKeyboardRemove()
        )

        # --- VIP Notification Check after bulk file processing ---
        chat_id = update.effective_chat.id
        await check_and_notify_vip_after_purchase(user_id, context, update.effective_chat.id)

    except Exception as e:
        logger.error(f"❌ خطا در خواندن یا پردازش فایل اکسل: {e}")
        await update.message.reply_text(f"❌ خطا در خواندن یا پردازش فایل اکسل: {e}")
    finally:
        # Ensure the temporary file is deleted
        if os.path.exists(file_download_path):
            os.remove(file_download_path)
            logger.info(f"Temporary uploaded bulk purchase file deleted: {file_download_path} ✅")

    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Cancels the ongoing conversation. ❌
    """
    await update.message.reply_text(
        "عملیات لغو شد. 🛑", reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END  # End the conversation 🔚


async def list_customers(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handles the /list_customers command. 👥
    Reads customer data from the user's Excel file, creates a temporary Excel file
    with only customer data, sends it, and then deletes the temporary file. 🗑️
    """
    user_id = update.effective_user.id
    excel_file_path = get_user_excel_path(user_id)

    if not os.path.exists(excel_file_path):
        await update.message.reply_text(
            "فایل داده‌ای یافت نشد. لطفاً ابتدا با /new_purchase خریدی را ثبت کنید. 😔"
        )
        return

    df_customers = excel_manager.get_customers_data(excel_file_path)
    if df_customers.empty:
        await update.message.reply_text("هنوز هیچ مشتری ثبت نشده است. 🤷‍♂️")
    else:
        # Create a temporary Excel file with customer data 📊
        temp_excel_path = excel_manager.create_temp_excel_report(
            df_customers, "Customers", "customers", DATA_DIR
        )
        await update.message.reply_text(
            "لیست مشتریان شما در فایل اکسل پیوست شده است: 📄"
        )
        await send_file_to_user(update, context, temp_excel_path)
        os.remove(temp_excel_path)  # Delete the temporary file after sending 🚮
        logger.info(f"Temporary customer report deleted: {temp_excel_path} ✅")


async def list_transactions(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handles the /list_transactions command. 💰
    Reads transaction data from the user's Excel file, creates a temporary Excel file
    with only transaction data, sends it, and then deletes the temporary file. 🗑️
    """
    user_id = update.effective_user.id
    excel_file_path = get_user_excel_path(user_id)

    if not os.path.exists(excel_file_path):
        await update.message.reply_text(
            "فایل داده‌ای یافت نشد. لطفاً ابتدا با /new_purchase خریدی را ثبت کنید. 😔"
        )
        return

    df_transactions = excel_manager.get_transactions_data(excel_file_path)
    if df_transactions.empty:
        await update.message.reply_text("هنوز هیچ تراکنشی ثبت نشده است. 🤷‍♀️")
    else:
        # Create a temporary Excel file with transaction data 📊
        temp_excel_path = excel_manager.create_temp_excel_report(
            df_transactions, "Transactions", "transactions", DATA_DIR
        )
        await update.message.reply_text(
            "تاریخچه تراکنش‌های شما در فایل اکسل پیوست شده است: 📄"
        )
        await send_file_to_user(update, context, temp_excel_path)
        os.remove(temp_excel_path)  # Delete the temporary file after sending 🚮
        logger.info(f"Temporary transaction report deleted: {temp_excel_path} ✅")

# --- Import historical transactions from Excel file ---
def convert_to_shamsi_if_needed(date_str):
    """
    اگر تاریخ میلادی بود به شمسی تبدیل کن. اگر خودش شمسی بود و معتبر بود، همون رو بده.
    خروجی همیشه به صورت yyyy-mm-dd
    """
    try:
        parsed = pd.to_datetime(date_str, errors='raise')
        shamsi = jdatetime.date.fromgregorian(date=parsed.date())
        return f"{shamsi.year}-{shamsi.month:02}-{shamsi.day:02}"
    except Exception:
        # فرض بر این که خودش شمسی بوده
        try:
            y, m, d = map(int, date_str.split("-"))
            _ = jdatetime.date(y, m, d)  # اگر ایراد داشت، اینجا خطا میده
            return f"{y}-{m:02}-{d:02}"
        except Exception:
            raise ValueError(f"تاریخ '{date_str}' معتبر نیست.")


# --- Import historical transactions from Excel file ---
def convert_to_shamsi_if_needed(date_input):
    """
    Converts a date string (Gregorian or Shamsi) to a Shamsi date string (YYYY-MM-DD).
    Handles NaN values and invalid date strings gracefully.
    Returns 'N/A' for invalid or NaN dates.
    """
    if pd.isna(date_input) or str(date_input).strip().lower() == 'nan':
        return 'N/A' # Explicitly handle NaN
    
    date_str = str(date_input).strip()

    try:
        # Try parsing as Gregorian first
        parsed = pd.to_datetime(date_str, errors='coerce')
        if pd.notna(parsed):
            shamsi = jdatetime.date.fromgregorian(date=parsed.date())
            return f"{shamsi.year}-{shamsi.month:02}-{shamsi.day:02}"
    except Exception:
        pass # Fall through to try as Shamsi

    try:
        # Assume it's already Shamsi
        y, m, d = map(int, date_str.split("-"))
        _ = jdatetime.date(y, m, d)  # Validate if it's a valid Shamsi date
        return f"{y}-{m:02}-{d:02}"
    except Exception:
        pass # Fall through to return N/A

    return 'N/A' # If neither works, return 'N/A'


def import_transactions_from_excel(user_id, file_path):
    """
    Imports past customer transactions from a user-provided Excel file.
    Expected columns: نام مشتری، شماره تماس، مبلغ (تومان)، تاریخ خرید
    """
    excel_path = get_user_excel_path(user_id)

    # Load existing data or create empty DataFrames if file doesn't exist
    if os.path.exists(excel_path):
        customers_df = pd.read_excel(excel_path, sheet_name="Customers")
        transactions_df = pd.read_excel(excel_path, sheet_name="Transactions")
    else:
        # Create empty DataFrames with correct columns if the Excel file doesn't exist
        customers_df = pd.DataFrame(columns=["کد مشتری", "نام", "شماره تماس", "تاریخ عضویت", "توضیحات"])
        transactions_df = pd.DataFrame(columns=["شناسه مشتری", "تاریخ فاکتور", "شماره فاکتور", "مبلغ (تومان)"])
        # Ensure the Excel file is created if it doesn't exist before attempting to load/write
        excel_manager.create_initial_excel(excel_path)

    df_import = pd.read_excel(file_path) # Read the imported file
    required_cols = ["نام مشتری", "شماره تماس", "مبلغ (تومان)", "تاریخ خرید"]
    if not all(col in df_import.columns for col in required_cols):
        raise ValueError("فایل باید دارای ستون‌های: نام مشتری، شماره تماس، مبلغ (تومان)، تاریخ خرید باشد.")

    # Determine the starting invoice counter
    # Handle cases where 'شماره فاکتور' might be non-numeric or empty
    max_invoice_num = 0
    if not transactions_df.empty and "شماره فاکتور" in transactions_df.columns:
        # Extract numeric part, handle potential non-string values or NaNs
        existing_nums = transactions_df["شماره فاکتور"].dropna().astype(str).str.extract(r'INV(\d+)')[0]
        if not existing_nums.empty:
            max_invoice_num = max(pd.to_numeric(existing_nums, errors='coerce').dropna())
    
    invoice_counter = int(max_invoice_num) + 1 if pd.notna(max_invoice_num) else 100

    processed_rows = 0
    for _, row in df_import.iterrows():
        try:
            name = str(row["نام مشتری"]).strip()
            phone = str(row["شماره تماس"]).strip()

            # Safe conversion of amount
            amount_str = str(row["مبلغ (تومان)"]).replace(",", "").strip()
            amount = int(float(amount_str)) # Convert to float first to handle decimals from excel, then to int

            # Date conversion (might be Gregorian or Shamsi)
            date_raw = row["تاریخ خرید"] # Keep as is, let helper function handle type
            date = convert_to_shamsi_if_needed(date_raw)

            if date == 'N/A':
                logger.warning(f"Skipping row due to invalid date: {row.to_dict()}")
                continue # Skip this row if date is invalid

        except Exception as e:
            logger.error(f"خطا در خواندن سطر: {row.to_dict()} → {e}")
            continue # Skip row on error

        # Check for existing customer
        existing_customer = customers_df[
            (customers_df["نام"] == name) & (customers_df["شماره تماس"] == phone)
        ]

        customer_id = None
        if not existing_customer.empty:
            customer_id = existing_customer.iloc[0]["کد مشتری"]
        else:
            # Generate new customer ID
            last_id = 0
            if not customers_df.empty and "کد مشتری" in customers_df.columns:
                existing_customer_ids_numeric_str = customers_df["کد مشتری"].dropna().astype(str).str.extract(r'C(\d+)')[0]
                if not existing_customer_ids_numeric_str.empty:
                    last_id = max(pd.to_numeric(existing_customer_ids_numeric_str, errors='coerce').dropna().astype(int))

            customer_id = f"C{last_id + 1:03}"
            new_customer = {
                "کد مشتری": customer_id,
                "نام": name,
                "شماره تماس": phone,
                "تاریخ عضویت": date, # Use the converted date here
                "توضیحات": "",
            }
            customers_df = pd.concat([customers_df, pd.DataFrame([new_customer])], ignore_index=True)

        new_transaction = {
            "شناسه مشتری": customer_id,
            "تاریخ فاکتور": date, # Use the converted date here
            "شماره فاکتور": f"INV{invoice_counter:03}", # Format invoice number
            "مبلغ (تومان)": amount,
        }
        transactions_df = pd.concat([transactions_df, pd.DataFrame([new_transaction])], ignore_index=True)
        invoice_counter += 1
        processed_rows += 1

    # Save the updated DataFrames to the Excel file
    # Use mode='w' to overwrite the file and if_sheet_exists='replace'
    with pd.ExcelWriter(excel_path, engine='openpyxl', mode='w') as writer:
        customers_df.to_excel(writer, sheet_name="Customers", index=False)
        transactions_df.to_excel(writer, sheet_name="Transactions", index=False)
    
    return processed_rows, len(customers_df), len(transactions_df)

# این متغیر در ConversationHandler استفاده خواهد شد
WAITING_FOR_IMPORT_FILE = 9999  # باید عددی منحصر به‌فرد باشه خارج از مقادیر دیگر state ها

async def import_transactions_entry_point(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "لطفاً فایل اکسل تراکنش‌های گذشته را ارسال کنید. 📄\n\n"
        "فایل باید دارای ستون‌های زیر باشد:\n"
        "- نام مشتری\n- شماره تماس\n- مبلغ (تومان)\n- تاریخ خرید\n\n"
        "پس از دریافت فایل، عملیات وارد کردن آغاز خواهد شد.",
        reply_markup=ReplyKeyboardRemove()
    )
    return WAITING_FOR_IMPORT_FILE


async def handle_import_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    document = update.message.document

    if not document.file_name.endswith(".xlsx"):
        await update.message.reply_text("فایل باید با فرمت .xlsx باشد.")
        # Allow user to send correct file or cancel, stay in state
        return WAITING_FOR_IMPORT_FILE

    file_path = os.path.join(DATA_DIR, str(user_id), "imported_transactions.xlsx")
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    # دانلود فایل
    file = await document.get_file()
    await file.download_to_drive(file_path)

    try:
        imported_count, updated_customers, updated_transactions = import_transactions_from_excel(user_id, file_path)
        await update.message.reply_text(
            f"✅ عملیات وارد کردن تراکنش‌ها با موفقیت انجام شد!\n\n"
            f"🔢 تعداد ردیف‌های ورودی: {imported_count}\n"
            f"👥 تعداد کل مشتریان (پس از بروزرسانی): {updated_customers}\n"
            f"🧾 تعداد کل تراکنش‌ها (پس از بروزرسانی): {updated_transactions}"
        )
        # After successful import, also run VIP notification check
        await check_and_notify_vip_after_purchase(user_id, context, update.effective_chat.id)
        
    except Exception as e:
        logger.error(f"❌ خطا در پردازش فایل: {e}")
        await update.message.reply_text(f"❌ خطا در پردازش فایل: {e}")
    finally:
        if os.path.exists(file_path):
            os.remove(file_path) # Clean up the uploaded file
            logger.info(f"Temporary imported transactions file deleted: {file_path} ✅")


    return ConversationHandler.END


# async def analyze_data(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     """
#     Handles the /analyze_data command. 📊
#     Performs customer analysis based on transaction data and sends the report as text. 📈
#     """
#     user_id = update.effective_user.id
#     excel_file_path = get_user_excel_path(user_id)

#     # Check if the Excel file exists for the user 🔍
#     if not os.path.exists(excel_file_path):
#         await update.message.reply_text("فایل داده‌ای برای تحلیل یافت نشد. لطفاً ابتدا با /new_purchase خریدی را ثبت کنید. 😔")
#         return

#     df_transactions = excel_manager.get_transactions_data(excel_file_path)
#     df_customers = excel_manager.get_customers_data(excel_file_path)  # Load customer data

#     # Ensure there are enough transactions for meaningful analysis (e.g., at least 5) 📉
#     if df_transactions.empty or len(df_transactions) < 5:
#         await update.message.reply_text("تراکنش‌های کافی برای انجام تحلیل معنی‌دار وجود ندارد. لطفاً خریدهای بیشتری را ثبت کنید. 📊")
#         return

#     # Perform analysis using data_analyzer module and get the report string 🧠
#     # Pass both dataframes to perform_analysis
#     analysis_report = data_analyzer.perform_analysis(df_transactions, df_customers)

#     await update.message.reply_text(f"گزارش تحلیل مشتریان شما:\n{analysis_report}")


# --- Analyze Data Conversation Handlers ---
SELECT_ANALYSIS_MENU = 4000
SELECT_SEGMENT_TYPE = 4001
SELECT_CHART_TYPE = 4002

async def analyze_data_entry_point(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    excel_file_path = get_user_excel_path(user_id)

    if not os.path.exists(excel_file_path):
        await update.message.reply_text("فایل داده‌ای برای تحلیل یافت نشد. لطفاً ابتدا با /new_purchase خریدی را ثبت کنید. 😔")
        return ConversationHandler.END

    df_transactions = excel_manager.get_transactions_data(excel_file_path)
    df_customers = excel_manager.get_customers_data(excel_file_path)

    if df_transactions.empty or len(df_transactions) < 5:
        await update.message.reply_text("تراکنش‌های کافی (حداقل ۵ تراکنش) برای انجام تحلیل معنی‌دار وجود ندارد. لطفاً خریدهای بیشتری را ثبت کنید. 📋")
        return ConversationHandler.END

    full_segmented_df = data_analyzer.get_full_customer_segments_df(df_transactions, df_customers)
    if full_segmented_df.empty:
        await update.message.reply_text("خطا در انجام تحلیل مشتریان. لطفاً از صحت داده‌ها اطمینان حاصل کنید. ⛔")
        return ConversationHandler.END

    context.user_data["full_segmented_df"] = full_segmented_df

    keyboard = [
        [KeyboardButton("👥 تحلیل"), KeyboardButton("📊 گزارش")],  # کنار هم
        [KeyboardButton("⬅️ خروج")]  # زیرش
    ]

    await update.message.reply_text(
        "چه کاری می‌خوای انجام بدی؟ 👇",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )
    return SELECT_ANALYSIS_MENU

async def handle_analysis_menu_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()

    if text == "👥 تحلیل":
        return await show_segment_buttons(update, context)
    elif text == "📊 گزارش":
        return await show_chart_buttons(update, context)
    elif text == "⬅️ خروج":
        await update.message.reply_text("از منوی تحلیل خارج شدی. 📛", reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END
    else:
        await update.message.reply_text("لطفاً یکی از گزینه‌های منو را انتخاب کن.")
        return SELECT_ANALYSIS_MENU

async def show_segment_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    keyboard = [
        [KeyboardButton("ویژه 🏆")],
        [KeyboardButton("وفادار ✨")],
        [KeyboardButton("امید بخش 🌱")],
        [KeyboardButton("در خطر ⚠️")],
        [KeyboardButton("غیر فعال 💩")],
        [KeyboardButton("از دست رفته 🗑️")],
        [KeyboardButton("معمولی 🤝")],
        [KeyboardButton("فاقد تراکنش 🤷")],
        [KeyboardButton("🔙 بازگشت")]
    ]
    await update.message.reply_text("دسته‌بندی مد نظرت رو انتخاب کن:", reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
    return SELECT_SEGMENT_TYPE

async def show_chart_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    keyboard = [
        [KeyboardButton("📊 نمودار دسته‌های رفتاری")],
        [KeyboardButton("📈 نمودار فعالیت زمانی")],
        [KeyboardButton("🔙 بازگشت")]
    ]
    await update.message.reply_text("کدوم نمودار رو می‌خوای ببینی؟", reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
    return SELECT_CHART_TYPE
    
async def send_segment_excel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Receives the selected segment type from Reply Keyboard message
    and sends the corresponding Excel file or a message explaining conditions.
    """
    # Get the selected segment name directly from the message text
    selected_segment_button_text = update.message.text

    # Map button text (with emoji) back to pure segment name
    segment_name_map = {
        "ویژه 🏆": "ویژه",
        "وفادار ✨": "وفادار",
        "امید بخش 🌱": "امید بخش",
        "در خطر ⚠️": "در خطر",
        "غیر فعال 💤": "غیر فعال",
        "از دست رفته 🗑️": "از دست رفته",
        "معمولی 🤝": "معمولی",
        "فاقد تراکنش 🤷": "فاقد تراکنش",
        "خروج ⬅️": "خروج",
    }
    selected_segment_name = segment_name_map.get(selected_segment_button_text)

    # Define descriptions and conditions for each segment
    segment_info = {
        "ویژه": {
            "description": "مشتریانی با بالاترین ارزش، فعال با خریدهای زیاد و گران. این مشتریان حیاتی هستند و باید تشویق و حفظ شوند. 💎"
        },
        "وفادار": {
            "description": "مشتریان فعال با سابقه خرید خوب و مناسب برای پاداش و ارتباط مداوم. ✨"
        },
        "امید بخش": {
            "description": "تازه‌واردها یا مشتریانی با پتانسیل بالا که نیاز به پرورش و انگیزش دارند. 🌱",
        },
        "در خطر": {
            "description": "مشتریانی که قبلاً خوب بوده‌اند اما مدتی است خرید نکرده‌اند یا کمتر فعال بوده‌اند و در معرض خطر ریزش هستند. ⚠️"
        },
        "غیر فعال": {
            "description": "مشتریانی که برای مدت طولانی هیچ خریدی نداشته‌اند. 💤"
        },
        "از دست رفته": {"description": "مشتریانی که به احتمال زیاد دیگر برنمی‌گردند. 🗑️"},
        "معمولی": {
            "description": "سایر مشتریان که در دسته‌بندی‌های دیگر قرار نمی‌گیرند. 🤝"
        },
        "فاقد تراکنش": {
            "description": "مشتریانی که هیچ تراکنشی در سیستم ثبت نکرده‌اند. 🤷"
        },
    }

    if selected_segment_name == "خروج":
        await update.message.reply_text(
            "عملیات تحلیل لغو شد. 🛑", reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END

    full_segmented_df = context.user_data.get("full_segmented_df")
    if full_segmented_df is None or full_segmented_df.empty:
        await update.message.reply_text(
            "اطلاعات تحلیل مشتریان موجود نیست. لطفاً دوباره /analyze_data را اجرا کنید. 😔",
            reply_markup=ReplyKeyboardRemove(),
        )
        return ConversationHandler.END

    # Filter DataFrame for the selected segment
    segment_df = full_segmented_df[
        full_segmented_df["دسته رفتاری نهایی"] == selected_segment_name
    ]

    if segment_df.empty:
        # Get description and condition for the selected segment
        info = segment_info.get(
            selected_segment_name,
            {
                "description": "توضیحات این بخش در دسترس نیست.",
            },
        )
        response_message = (
            f"متاسفانه هیچ مشتری‌ای در بخش '{selected_segment_name}' یافت نشد. \n\n"
            f"*{info['description']}*\n"
            "برای مشاهده تحلیل این بخش، مشتریان شما باید به شرایط فوق دست یابند. 📈"
        )
        await update.message.reply_text(
            response_message, parse_mode="Markdown"
        )
        return SELECT_SEGMENT_TYPE


    # Columns to include in the output Excel file for each segment, as per "لیست مشتری‌ها.pdf" structure
    output_columns_map = {
        "کد مشتری": "Customer ID",
        "نام مشتری": "Name",
        "شماره تماس": "Phone",
        "تاریخ عضویت": "Registration Date",
        "تعداد خرید": "Total Transactions",  # This is Frequency from RFM
        "مجموع خرید": "Total Spend",  # This is Monetary from RFM
    }

    present_columns = [
        col for col in output_columns_map.keys() if col in segment_df.columns
    ]
    segment_output_df = segment_df[present_columns].rename(columns=output_columns_map)

    # Generate temporary Excel file
    user_id = update.effective_user.id
    temp_excel_path = excel_manager.create_temp_excel_report(
        segment_output_df,
        selected_segment_name,
        f"customer_segment_{selected_segment_name}",
        DATA_DIR,
    )

    await update.message.reply_text(
        f"لیست مشتریان بخش '{selected_segment_name}' در فایل اکسل پیوست شده است: 📄",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton("ویژه 🏆")],
                [KeyboardButton("وفادار ✨")],
                [KeyboardButton("امید بخش 🌱")],
                [KeyboardButton("در خطر ⚠️")],
                [KeyboardButton("غیر فعال 💤")],
                [KeyboardButton("از دست رفته 🗑️")],
                [KeyboardButton("معمولی 🤝")],
                [KeyboardButton("فاقد تراکنش 🤷")],
                [KeyboardButton("📊 RFM Pie Chart")],
                [KeyboardButton("📊 TAM Bar Chart")],
                [KeyboardButton("خروج ⬅️")],
            ],
            resize_keyboard=True,
            one_time_keyboard=False,
        )
    )
    await send_file_to_user(
        update, context, temp_excel_path, caption=f"مشتریان بخش {selected_segment_name}"
    )

    os.remove(temp_excel_path)  # Clean up the temporary file
    logger.info(f"Temporary segment report deleted: {temp_excel_path} ✅")

    return SELECT_SEGMENT_TYPE


async def get_full_excel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handles the /get_full_excel command. 📄
    Sends the user's main Excel file containing all sheets.
    """
    user_id = update.effective_user.id
    excel_file_path = get_user_excel_path(user_id)

    if not os.path.exists(excel_file_path):
        await update.message.reply_text(
            "فایل اکسل اصلی شما یافت نشد. لطفاً ابتدا با /new_purchase خریدی را ثبت کنید. 😔"
        )
        return

    await update.message.reply_text("فایل اکسل کامل شما در حال ارسال است: 📥")
    await send_file_to_user(
        update, context, excel_file_path, caption="فایل اکسل کامل شما:"
    )


# Pie chart handler
async def send_rfm_pie_chart(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    user_id = update.effective_user.id
    file_path = get_user_excel_path(user_id)

    def load_data_from_excel(excel_path):
        df_customers = pd.read_excel(excel_path, sheet_name="Customers")
        df_transactions = pd.read_excel(excel_path, sheet_name="Transactions")
        return df_customers, df_transactions

    if not os.path.exists(file_path):
        await update.message.reply_text("❌ شما هنوز اطلاعات خرید ثبت نکردید.")
        return

    df_customers, df_transactions = load_data_from_excel(file_path)
    df_segmented = get_full_customer_segments_df(df_transactions, df_customers)

    if df_segmented.empty:
        await update.message.reply_text("هیچ داده‌ای برای تحلیل یافت نشد.")
        return

    pie_chart_buffer = create_rfm_pie_chart(df_segmented)

    await update.message.reply_photo(
        photo=pie_chart_buffer, caption="📊 نمودار درصدی دسته‌های رفتاری مشتریان"
    )


# Bar chart handler
async def send_tam_bar_chart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    file_path = get_user_excel_path(user_id)

    def load_data_from_excel(excel_path):
        df_customers = pd.read_excel(excel_path, sheet_name="Customers")
        df_transactions = pd.read_excel(excel_path, sheet_name="Transactions")
        return df_customers, df_transactions

    if not os.path.exists(file_path):
        await update.message.reply_text("❌ اطلاعات خریدی ثبت نشده.")
        return

    df_customers, df_transactions = load_data_from_excel(file_path)
    df_segmented = get_full_customer_segments_df(df_transactions, df_customers)

    if df_segmented.empty:
        await update.message.reply_text("داده‌ای برای تحلیل یافت نشد.")
        return

    chart_buffer = create_tam_bar_chart(df_segmented)

    await update.message.reply_photo(
        photo=chart_buffer, caption="📊 نمودار وضعیت‌های زمانی TAM"
    )


# Start scheduler
async def post_init(application):
    start_scheduler(application)


def main() -> None:
    """
    Main function to set up and run the Telegram bot. 🚀
    Initializes the Application, adds handlers for commands and messages, and starts polling.
    """
    # Create the Application and pass it your bot's token. 🤖
    application = Application.builder().token(BOT_TOKEN).post_init(post_init).build()

    # --- Register Handlers 🔗 ---

    # Command handler for /new_purchase (now the entry point for mode selection)
    # application.add_handler(CommandHandler("new_purchase", new_purchase_entry_point))

    # ConversationHandler for /new_purchase command 💬
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("new_purchase", new_purchase_entry_point)],
        states={
            SELECT_ENTRY_MODE: [
                MessageHandler(filters.Text("ثبت خرید تکی ➕"), select_single_entry),
                MessageHandler(
                    filters.Text("ثبت چند خرید (وزودی متنی) 📝"), show_bulk_input_format
                ),
                MessageHandler(filters.Text("ثبت خرید با فایل اکسل 📄"), start_file_upload_flow),
                MessageHandler(filters.Text("خروج ⬅️"), cancel),
            ],
            SINGLE_CUSTOMER_NAME: [
                    MessageHandler(filters.Text("خروج ⬅️"), cancel),
                    MessageHandler(filters.TEXT & ~filters.COMMAND, get_single_customer_name)
            ],
            SINGLE_CUSTOMER_PHONE: [
                MessageHandler(filters.Text("خروج ⬅️"), cancel),
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND, get_single_customer_phone
                )
            ],
            SINGLE_PURCHASE_AMOUNT: [
                MessageHandler(filters.Text("خروج ⬅️"), cancel),
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND, get_single_purchase_amount
                )
            ],
            BULK_PURCHASE_DATA: [
                MessageHandler(filters.Text("خروج ⬅️"), cancel),
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_bulk_purchase_data)
            ],
            WAITING_FOR_BULK_FILE: [
                MessageHandler(filters.Text("خروج ⬅️"), cancel),
                MessageHandler(filters.Document.FileExtension("xlsx"), handle_bulk_purchase_file)
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel)
        ],  # Allows user to cancel the conversation 🛑
        allow_reentry=True,  # اجازه ورود چندباره
        per_message=False,  # فقط بر اساس وضعیت فعلی رفتار کن
    )
    application.add_handler(conv_handler)

    # ConversationHandler for /analyze_data command 📊
    analysis_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("analyze_data", analyze_data_entry_point)],
        states={

            # مرحله اول: منوی کلی تحلیل
            SELECT_ANALYSIS_MENU: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_analysis_menu_choice)
            ],

            # مرحله دوم: نمایش دسته‌بندی‌ها
            SELECT_SEGMENT_TYPE: [
                MessageHandler(filters.Text("🔙 بازگشت"), analyze_data_entry_point),  # برگشت به منوی اول
                MessageHandler(filters.TEXT & ~filters.COMMAND, send_segment_excel)
            ],

            # مرحله سوم: نمایش نمودارها
            SELECT_CHART_TYPE: [
                MessageHandler(filters.Text("🔙 بازگشت"), analyze_data_entry_point),  # برگشت به منوی اول
                MessageHandler(filters.Text("📊 نمودار دسته‌های رفتاری"), send_rfm_pie_chart),
                MessageHandler(filters.Text("📈 نمودار فعالیت زمانی"), send_tam_bar_chart),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True,
    )
    application.add_handler(analysis_conv_handler)
    
    # هندلر مخصوص بارگذاری تراکنش‌های قدیمی
    import_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("import_transactions", import_transactions_entry_point)],
        states={
            WAITING_FOR_IMPORT_FILE: [MessageHandler(filters.Document.FileExtension("xlsx") & filters.Document.MimeType("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"), handle_import_file)]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_message=False,
        allow_reentry=True,
    )
    application.add_handler(import_conv_handler)


    # Existing handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.CONTACT, handle_contact))
    application.add_handler(CommandHandler("list_customers", list_customers))
    application.add_handler(CommandHandler("list_transactions", list_transactions))
    # application.add_handler(CommandHandler("analyze_data", analyze_data))
    application.add_handler(CommandHandler("get_full_excel", get_full_excel))
    application.add_handler(CommandHandler("import_transactions", import_transactions_entry_point))

    # Run the bot until the user presses Ctrl-C 🏃‍♂️
    logger.info("Bot started polling... 🟢")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
