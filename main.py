# main.py
import logging
import os
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

# Import custom modules 📚
import excel_manager
import user_manager
import data_analyzer
from dotenv import load_dotenv

# Import custom modules 📚
import excel_manager
import user_manager
import data_analyzer

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
CUSTOMER_NAME, CUSTOMER_PHONE, PURCHASE_AMOUNT = range(3)

# --- Helper Functions 🛠️ ---
def get_user_excel_path(user_id):
    """
    Returns the path to the user's dedicated Excel file. 📄
    Each user gets a unique Excel file based on their Telegram user ID.
    """
    return os.path.join(DATA_DIR, f"{user_id}.xlsx")

async def send_file_to_user(update: Update, context: ContextTypes.DEFAULT_TYPE, file_path: str, caption: str = ""):
    """
    Sends the specified file to the user. 📤
    Handles FileNotFoundError and other potential exceptions during file sending.
    """
    try:
        # Open the file in binary read mode and send it as a document 📂
        await update.message.reply_document(document=open(file_path, 'rb'), caption=caption)
    except FileNotFoundError:
        logger.error(f"File not found at {file_path} ❌")
        await update.message.reply_text("خطا: فایل یافت نشد. لطفاً دوباره تلاش کنید یا با پشتیبانی تماس بگیرید. 😟")
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

    # Check if the user's phone number is already saved ✅
    if not user_manager.get_user_phone(user.id):
        # If not, request the phone number using a special keyboard button 📱
        keyboard = [[KeyboardButton("اشتراک گذاری شماره تماس", request_contact=True)]]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
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
            "/list_customers - مشاهده لیست مشتریان 👥\n"
            "/list_transactions - مشاهده تاریخچه تراکنش‌ها 💰\n"
            "/analyze_data - دریافت تحلیل مشتریان 📊\n"
            "/get_full_excel - دریافت فایل اکسل کامل 📄\n", # Added new command
            reply_markup=ReplyKeyboardRemove() # Remove the phone number sharing keyboard 🧹
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
        logger.info(f"User {user.id} ({user.first_name}) shared phone number: {phone_number} ✅")

        excel_file_path = get_user_excel_path(user.id)
        # Create the initial Excel file if it does not exist for this user 🆕
        if not os.path.exists(excel_file_path):
            excel_manager.create_initial_excel(excel_file_path)
            await update.message.reply_text(f"فایل داده‌های شما ایجاد شد. آماده استفاده هستید! 🎉")
        else:
            await update.message.reply_text("خوش آمدید! فایل داده‌های شما آماده است. 👍")

        # Display main commands after successful registration/login 🚀
        await update.message.reply_text(
            "اکنون می‌توانید از دستورات زیر استفاده کنید:\n"
            "/new_purchase - ثبت خرید جدید 🛒\n"
            "/list_customers - مشاهده لیست مشتریان 👥\n"
            "/list_transactions - مشاهده تاریخچه تراکنش‌ها 💰\n"
            "/analyze_data - دریافت تحلیل مشتریان 📊\n"
            "/get_full_excel - دریافت فایل اکسل کامل 📄\n", # Added new command
            reply_markup=ReplyKeyboardRemove() # Remove the phone number sharing keyboard 🧹
        )
    else:
        await update.message.reply_text("لطفاً شماره تماس خودتان را به اشتراک بگذارید. ☝️")

async def new_purchase_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Starts the conversation flow for registering a new purchase. 📝
    Checks if the user is registered (has a phone number).
    """
    user_id = update.effective_user.id
    if not user_manager.get_user_phone(user_id):
        await update.message.reply_text("لطفاً ابتدا با دستور /start شماره تماس خود را به اشتراک بگذارید. 📲")
        return ConversationHandler.END # End conversation if user is not registered 🛑

    await update.message.reply_text("لطفاً نام مشتری را وارد کنید: 🧑‍🤝‍🧑")
    return CUSTOMER_NAME # Move to the next state to get customer name ➡️

async def get_customer_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Gets the customer's name from the user and stores it in user_data. 💾
    Prompts for the customer's phone number next.
    """
    context.user_data["customer_name"] = update.message.text
    await update.message.reply_text("لطفاً شماره تلفن مشتری را وارد کنید: 📞")
    return CUSTOMER_PHONE # Move to the next state to get customer phone ➡️

async def get_customer_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Gets the customer's phone number, performs basic validation, and stores it. ✅
    Prompts for the purchase amount next.
    """
    phone_number = update.message.text.strip()
    # Basic validation for phone number (e.g., only digits, minimum length) 🔢
    if not phone_number.isdigit() or len(phone_number) < 8:
        await update.message.reply_text("شماره تلفن نامعتبر است. لطفاً یک شماره معتبر (فقط اعداد) وارد کنید: 🚫")
        return CUSTOMER_PHONE # Stay in the same state if validation fails 🔄
    
    context.user_data["customer_phone"] = phone_number
    await update.message.reply_text("لطفاً مبلغ خرید را (به تومان) وارد کنید: 💲")
    return PURCHASE_AMOUNT # Move to the next state to get purchase amount ➡️

async def get_purchase_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Gets the purchase amount, performs validation, and saves the purchase. 💰
    Sends the updated Excel file to the user upon successful recording.
    """
    try:
        amount = int(update.message.text)
        if amount <= 0:
            raise ValueError # Amount must be positive 📈
    except ValueError:
        await update.message.reply_text("مبلغ نامعتبر است. لطفاً یک عدد مثبت وارد کنید: 🔢")
        return PURCHASE_AMOUNT # Stay in the same state if validation fails 🔄

    user_id = update.effective_user.id
    excel_file_path = get_user_excel_path(user_id)

    customer_name = context.user_data["customer_name"]
    customer_phone = context.user_data["customer_phone"]

    # Call excel_manager to save the purchase details ✍️
    excel_manager.save_purchase(excel_file_path, customer_name, customer_phone, amount)

    await update.message.reply_text("خرید با موفقیت ثبت شد! 🎉")
    # await send_file_to_user(update, context, excel_file_path, caption="فایل اکسل به‌روز شده شما:") # Send the updated Excel file 📤
    return ConversationHandler.END # End the conversation ✅

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Cancels the ongoing conversation for new purchase registration. ❌
    """
    await update.message.reply_text("ثبت خرید لغو شد. 🛑", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END # End the conversation 🔚

async def list_customers(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handles the /list_customers command. 👥
    Reads customer data from the user's Excel file, creates a temporary Excel file
    with only customer data, sends it, and then deletes the temporary file. 🗑️
    """
    user_id = update.effective_user.id
    excel_file_path = get_user_excel_path(user_id)

    if not os.path.exists(excel_file_path):
        await update.message.reply_text("فایل داده‌ای یافت نشد. لطفاً ابتدا با /new_purchase خریدی را ثبت کنید. 😔")
        return

    df_customers = excel_manager.get_customers_data(excel_file_path)
    if df_customers.empty:
        await update.message.reply_text("هنوز هیچ مشتری ثبت نشده است. 🤷‍♂️")
    else:
        # Create a temporary Excel file with customer data 📊
        temp_excel_path = excel_manager.create_temp_excel_report(
            df_customers, "Customers", user_id, "customers", DATA_DIR
        )
        await update.message.reply_text("لیست مشتریان شما در فایل اکسل پیوست شده است: 📄")
        await send_file_to_user(update, context, temp_excel_path)
        os.remove(temp_excel_path) # Delete the temporary file after sending 🚮
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
        await update.message.reply_text("فایل داده‌ای یافت نشد. لطفاً ابتدا با /new_purchase خریدی را ثبت کنید. 😔")
        return

    df_transactions = excel_manager.get_transactions_data(excel_file_path)
    if df_transactions.empty:
        await update.message.reply_text("هنوز هیچ تراکنشی ثبت نشده است. 🤷‍♀️")
    else:
        # Create a temporary Excel file with transaction data 📊
        temp_excel_path = excel_manager.create_temp_excel_report(
            df_transactions, "Transactions", user_id, "transactions", DATA_DIR
        )
        await update.message.reply_text("تاریخچه تراکنش‌های شما در فایل اکسل پیوست شده است: 📄")
        await send_file_to_user(update, context, temp_excel_path)
        os.remove(temp_excel_path) # Delete the temporary file after sending 🚮
        logger.info(f"Temporary transaction report deleted: {temp_excel_path} ✅")


async def analyze_data(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handles the /analyze_data command. 📊
    Performs customer analysis based on transaction data and sends the report as text. 📈
    """
    user_id = update.effective_user.id
    excel_file_path = get_user_excel_path(user_id)

    # Check if the Excel file exists for the user 🔍
    if not os.path.exists(excel_file_path):
        await update.message.reply_text("فایل داده‌ای برای تحلیل یافت نشد. لطفاً ابتدا با /new_purchase خریدی را ثبت کنید. 😔")
        return

    df_transactions = excel_manager.get_transactions_data(excel_file_path)
    df_customers = excel_manager.get_customers_data(excel_file_path) # Load customer data

    # Ensure there are enough transactions for meaningful analysis (e.g., at least 5) 📉
    if df_transactions.empty or len(df_transactions) < 5:
        await update.message.reply_text("تراکنش‌های کافی برای انجام تحلیل معنی‌دار وجود ندارد. لطفاً خریدهای بیشتری را ثبت کنید. 📊")
        return

    # Perform analysis using data_analyzer module and get the report string 🧠
    # Pass both dataframes to perform_analysis
    analysis_report = data_analyzer.perform_analysis(df_transactions, df_customers)
    
    await update.message.reply_text(f"گزارش تحلیل مشتریان شما:\n{analysis_report}")

async def get_full_excel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handles the /get_full_excel command. 📄
    Sends the user's main Excel file containing all sheets.
    """
    user_id = update.effective_user.id
    excel_file_path = get_user_excel_path(user_id)

    if not os.path.exists(excel_file_path):
        await update.message.reply_text("فایل اکسل اصلی شما یافت نشد. لطفاً ابتدا با /new_purchase خریدی را ثبت کنید. 😔")
        return
    
    await update.message.reply_text("فایل اکسل کامل شما در حال ارسال است: 📥")
    await send_file_to_user(update, context, excel_file_path, caption="فایل اکسل کامل شما:")


def main() -> None:
    """
    Main function to set up and run the Telegram bot. 🚀
    Initializes the Application, adds handlers for commands and messages, and starts polling.
    """
    # Create the Application and pass it your bot's token. 🤖
    application = Application.builder().token(BOT_TOKEN).build()

    # --- Register Handlers 🔗 ---

    # Command handler for /start ▶️
    application.add_handler(CommandHandler("start", start))
    # Message handler for shared contact (phone number) 📞
    application.add_handler(MessageHandler(filters.CONTACT, handle_contact))

    # ConversationHandler for /new_purchase command 💬
    # This allows the bot to guide the user through a multi-step input process. ➡️
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("new_purchase", new_purchase_start)],
        states={
            CUSTOMER_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_customer_name)],
            CUSTOMER_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_customer_phone)],
            PURCHASE_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_purchase_amount)],
        },
        fallbacks=[CommandHandler("cancel", cancel)], # Allows user to cancel the conversation 🛑
    )
    application.add_handler(conv_handler)

    # Command handlers for other functionalities 📋
    application.add_handler(CommandHandler("list_customers", list_customers))
    application.add_handler(CommandHandler("list_transactions", list_transactions))
    application.add_handler(CommandHandler("analyze_data", analyze_data))
    application.add_handler(CommandHandler("get_full_excel", get_full_excel)) # Register the new command

    # Run the bot until the user presses Ctrl-C 🏃‍♂️
    logger.info("Bot started polling... 🟢")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()

