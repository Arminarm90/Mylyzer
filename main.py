# main.py
import logging
import os
import zipfile  # Import zipfile module for creating zip archives 📚
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from dotenv import load_dotenv
import pandas as pd # Import pandas for DataFrame manipulation

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
# New states for selecting entry mode and bulk data input
SELECT_ENTRY_MODE, SINGLE_CUSTOMER_NAME, SINGLE_CUSTOMER_PHONE, SINGLE_PURCHASE_AMOUNT, BULK_PURCHASE_DATA = range(5)
ANALYZE_DATA_ENTRY, SELECT_SEGMENT_TYPE = range(5, 7) # Start from 5 to avoid conflict with previous states

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
            "/analyze_data - تحلیل رفتار مشتری 📊\n"
            "/get_full_excel - دریافت فایل اکسل کامل 📄\n",
            reply_markup=ReplyKeyboardRemove()  # Remove the phone number sharing keyboard 🧹
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
            "/analyze_data - تحلیل رفتار مشتری 📊\n"
            "/get_full_excel - دریافت فایل اکسل کامل 📄\n",
            reply_markup=ReplyKeyboardRemove()  # Remove the phone number sharing keyboard 🧹
        )
    else:
        await update.message.reply_text("لطفاً شماره تماس خودتان را به اشتراک بگذارید. ☝️")

async def new_purchase_entry_point(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Starts the conversation flow for registering a new purchase by asking the user for the entry mode. 📝
    """
    user_id = update.effective_user.id
    if not user_manager.get_user_phone(user_id):
        await update.message.reply_text("لطفاً ابتدا با دستور /start شماره تماس خود را به اشتراک بگذارید. 📲")
        return ConversationHandler.END  # End conversation if user is not registered 🛑

    keyboard = [
        [KeyboardButton("ثبت خرید تکی ➕")],
        [KeyboardButton("ثبت چند خرید یکجا 📝")],
        [KeyboardButton("انصراف 🛑")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text(
        "لطفاً نحوه ورود اطلاعات خرید را انتخاب کنید:",
        reply_markup=reply_markup
    )
    return SELECT_ENTRY_MODE # Move to the state where user selects entry mode ➡️

async def select_single_entry(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Triggered when user selects "ثبت خرید تکی ➕".
    Prompts for customer name and moves to SINGLE_CUSTOMER_NAME state.
    """
    await update.message.reply_text("لطفاً نام مشتری را وارد کنید: 🧑‍💼")
    return SINGLE_CUSTOMER_NAME

async def get_single_customer_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Gets the customer's name for single entry and stores it in user_data. 💾
    Prompts for the customer's phone number next.
    """
    context.user_data["customer_name"] = update.message.text
    await update.message.reply_text("لطفاً شماره تلفن مشتری را وارد کنید: 📞")
    return SINGLE_CUSTOMER_PHONE # Move to the next state to get customer phone ➡️

async def get_single_customer_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Gets the customer's phone number for single entry, performs basic validation, and stores it. ✅
    Prompts for the purchase amount next.
    """
    phone_number = update.message.text.strip()
    # Basic validation for phone number (e.g., only digits, minimum length) 🔢
    if not phone_number.isdigit() or len(phone_number) < 8:
        await update.message.reply_text("شماره تلفن نامعتبر است. لطفاً یک شماره معتبر (فقط اعداد) وارد کنید: 🚫")
        return SINGLE_CUSTOMER_PHONE  # Stay in the same state if validation fails 🔄

    context.user_data["customer_phone"] = phone_number
    await update.message.reply_text("لطفاً مبلغ خرید را (به تومان) وارد کنید: 💲")
    return SINGLE_PURCHASE_AMOUNT  # Move to the next state to get purchase amount ➡️

async def get_single_purchase_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Gets the purchase amount for single entry, performs validation, and saves the purchase. 💰
    Sends the updated Excel file to the user upon successful recording.
    """
    try:
        amount = int(update.message.text)
        if amount <= 0:
            raise ValueError  # Amount must be positive 📈
    except ValueError:
        await update.message.reply_text("مبلغ نامعتبر است. لطفاً یک عدد مثبت وارد کنید: 🔢")
        return SINGLE_PURCHASE_AMOUNT  # Stay in the same state if validation fails 🔄

    user_id = update.effective_user.id
    excel_file_path = get_user_excel_path(user_id)

    customer_name = context.user_data["customer_name"]
    customer_phone = context.user_data["customer_phone"]

    # Call excel_manager to save the purchase details ✍️
    excel_manager.save_purchase(excel_file_path, customer_name, customer_phone, amount)

    await update.message.reply_text("خرید با موفقیت ثبت شد! 🎉")
    # await send_file_to_user(update, context, excel_file_path, caption="فایل اکسل به‌روز شده شما:") # Optional: Send the updated Excel file 📤
    return ConversationHandler.END  # End the conversation ✅


async def show_bulk_input_format(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
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

async def get_bulk_purchase_data(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Processes multiple customer/purchase entries provided in a single text message.
    """
    user_id = update.effective_user.id
    excel_file_path = get_user_excel_path(user_id)
    raw_data_lines = update.message.text.strip().split('\n')
    
    successful_entries = 0
    failed_entries = []

    for line_num, line in enumerate(raw_data_lines, 1):
        line = line.strip()
        if not line: # Skip empty lines
            continue
        
        parts = line.replace('،', ',').split(',')
        if len(parts) < 3 or len(parts) > 4: # Expected: name, phone, description (optional), amount
            failed_entries.append(f"خط {line_num}: فرمت نامعتبر. باید حداقل شامل نام، شماره تلفن، مبلغ باشد. (مثال: نام،شماره،توضیحات،مبلغ)")
            continue

        customer_name = parts[0].strip()
        customer_phone = parts[1].strip()
        description = parts[2].strip() if len(parts) == 4 else "" # Description is optional
        amount_str = parts[3].strip() if len(parts) == 4 else parts[2].strip() # Amount can be 3rd if no description

        # Basic validation for phone number and amount
        if not customer_phone.isdigit() or len(customer_phone) < 8:
            failed_entries.append(f"خط {line_num}: شماره تلفن '{customer_phone}' نامعتبر است.")
            continue
        
        try:
            amount = int(amount_str)
            if amount <= 0:
                raise ValueError
        except ValueError:
            failed_entries.append(f"خط {line_num}: مبلغ '{amount_str}' نامعتبر است. باید یک عدد مثبت باشد.")
            continue

        try:
            # Call excel_manager to save the customer and purchase details
            excel_manager.save_purchase_bulk(excel_file_path, customer_name, customer_phone, amount, description) # Assuming description can be passed now
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

    await update.message.reply_text(response_message, reply_markup=ReplyKeyboardRemove())
    # Optional: Send the updated Excel file after bulk processing
    # await send_file_to_user(update, context, excel_file_path, caption="فایل اکسل به‌روز شده شما:")
    return ConversationHandler.END # End the conversation ✅

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Cancels the ongoing conversation. ❌
    """
    await update.message.reply_text("عملیات لغو شد. 🛑", reply_markup=ReplyKeyboardRemove())
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
        await update.message.reply_text("فایل داده‌ای یافت نشد. لطفاً ابتدا با /new_purchase خریدی را ثبت کنید. 😔")
        return

    df_customers = excel_manager.get_customers_data(excel_file_path)
    if df_customers.empty:
        await update.message.reply_text("هنوز هیچ مشتری ثبت نشده است. 🤷‍♂️")
    else:
        # Create a temporary Excel file with customer data 📊
        temp_excel_path = excel_manager.create_temp_excel_report(
            df_customers, "Customers", "customers", DATA_DIR
        )
        await update.message.reply_text("لیست مشتریان شما در فایل اکسل پیوست شده است: 📄")
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
        await update.message.reply_text("فایل داده‌ای یافت نشد. لطفاً ابتدا با /new_purchase خریدی را ثبت کنید. 😔")
        return

    df_transactions = excel_manager.get_transactions_data(excel_file_path)
    if df_transactions.empty:
        await update.message.reply_text("هنوز هیچ تراکنشی ثبت نشده است. 🤷‍♀️")
    else:
        # Create a temporary Excel file with transaction data 📊
        temp_excel_path = excel_manager.create_temp_excel_report(
            df_transactions, "Transactions", "transactions", DATA_DIR
        )
        await update.message.reply_text("تاریخچه تراکنش‌های شما در فایل اکسل پیوست شده است: 📄")
        await send_file_to_user(update, context, temp_excel_path)
        os.remove(temp_excel_path)  # Delete the temporary file after sending 🚮
        logger.info(f"Temporary transaction report deleted: {temp_excel_path} ✅")

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
async def analyze_data_entry_point(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handles the /analyze_data command. 📊
    Performs customer analysis, stores the full segmented DataFrame,
    and displays segment buttons.
    """
    user_id = update.effective_user.id
    excel_file_path = get_user_excel_path(user_id)

    if not os.path.exists(excel_file_path):
        await update.message.reply_text("فایل داده‌ای برای تحلیل یافت نشد. لطفاً ابتدا با /new_purchase خریدی را ثبت کنید. 😔")
        return ConversationHandler.END

    df_transactions = excel_manager.get_transactions_data(excel_file_path)
    df_customers = excel_manager.get_customers_data(excel_file_path)

    if df_transactions.empty or len(df_transactions) < 5:
        await update.message.reply_text("تراکنش‌های کافی (حداقل ۵ تراکنش) برای انجام تحلیل معنی‌دار وجود ندارد. لطفاً خریدهای بیشتری را ثبت کنید. �")
        return ConversationHandler.END

    # Perform full segmentation
    full_segmented_df = data_analyzer.get_full_customer_segments_df(df_transactions, df_customers)
    if full_segmented_df.empty:
        await update.message.reply_text("خطا در انجام تحلیل مشتریان. لطفاً از صحت داده‌ها اطمینان حاصل کنید. 🚫")
        return ConversationHandler.END
    
    # Store the full segmented DataFrame in user_data for later access
    context.user_data['full_segmented_df'] = full_segmented_df

    # Get unique segments to create buttons
    # Filter out "فاقد تراکنش" if no customers fall into it, or just show all
    available_segments = full_segmented_df['دسته رفتاری نهایی'].unique().tolist()
    
    # Define the desired order for buttons
    segment_button_order = [
        "ویژه 🏆", "وفادار ✨", "امید بخش 🌱", "در خطر ⚠️", 
        "غیر فعال 💤", "از دست رفته 🗑️", "معمولی 🤝", "فاقد تراکنش 🤷"
    ]
    
    # Create keyboard layout - 2 buttons per row for better display
    keyboard = []
    current_row = []
    for segment_label in segment_button_order:
        # Check if this segment actually exists in the data before creating a button
        if segment_label.replace(' 🏆', '').replace(' ✨', '').replace(' 🌱', '').replace(' ⚠️', '').replace(' 💤', '').replace(' 🗑️', '').replace(' 🤝', '').replace(' 🤷', '') in available_segments:
            current_row.append(KeyboardButton(segment_label))
            if len(current_row) == 2: # 2 buttons per row
                keyboard.append(current_row)
                current_row = []
    if current_row: # Add any remaining buttons
        keyboard.append(current_row)
    
    keyboard.append([KeyboardButton("انصراف 🛑")]) # Add a cancel button

    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text(
        "تحلیل مشتریان انجام شد! لطفاً برای مشاهده لیست مشتریان هر بخش، دکمه مربوطه را انتخاب کنید: 👇",
        reply_markup=reply_markup
    )
    return SELECT_SEGMENT_TYPE

async def send_segment_excel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Receives the selected segment type and sends the corresponding Excel file.
    """
    selected_segment_button_text = update.message.text
    # Remove emojis to get the actual segment name for filtering
    segment_name_map = {
        "ویژه 🏆": "ویژه",
        "وفادار ✨": "وفادار",
        "امید بخش 🌱": "امید بخش",
        "در خطر ⚠️": "در خطر",
        "غیر فعال 💤": "غیر فعال",
        "از دست رفته 🗑️": "از دست رفته",
        "معمولی 🤝": "معمولی",
        "فاقد تراکنش 🤷": "فاقد تراکنش",
        "انصراف 🛑": "انصراف" # Handle cancel here as well for consistency
    }
    
    selected_segment_name = segment_name_map.get(selected_segment_button_text)

    if selected_segment_name == "انصراف":
        await update.message.reply_text("عملیات تحلیل لغو شد. 🛑", reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END

    if selected_segment_name not in context.user_data.get('full_segmented_df', pd.DataFrame())['دسته رفتاری نهایی'].unique().tolist():
         await update.message.reply_text("بخش انتخاب شده معتبر نیست یا مشتری‌ای در آن بخش یافت نشد. لطفاً دوباره تلاش کنید. 🔄", reply_markup=ReplyKeyboardRemove())
         return ConversationHandler.END

    full_segmented_df = context.user_data.get('full_segmented_df')
    if full_segmented_df is None or full_segmented_df.empty:
        await update.message.reply_text("اطلاعات تحلیل مشتریان موجود نیست. لطفاً دوباره /analyze_data را اجرا کنید. 😔", reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END

    # Filter DataFrame for the selected segment
    segment_df = full_segmented_df[full_segmented_df['دسته رفتاری نهایی'] == selected_segment_name]

    if segment_df.empty:
        await update.message.reply_text(f"هیچ مشتری در بخش '{selected_segment_name}' یافت نشد. 🤷‍♂️", reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END
    
    # Columns to include in the output Excel file for each segment, as per "لیست مشتری‌ها.pdf" structure
    # Customer ID, Name, Phone, Registration Date, Total Transactions, Total Spend
    # Map these to the Persian column names from data_analyzer.get_full_customer_segments_df output
    output_columns_map = {
        'کد مشتری': 'Customer ID',
        'نام مشتری': 'Name',
        'شماره تماس': 'Phone',
        'تاریخ عضویت': 'Registration Date',
        'تعداد خرید': 'Total Transactions', # This is Frequency from RFM
        'مجموع خرید': 'Total Spend' # This is Monetary from RFM
    }
    
    # Ensure all required columns exist in segment_df before selecting
    # Some columns might not exist if data_analyzer.py or excel_manager.py outputs changed
    present_columns = [col for col in output_columns_map.keys() if col in segment_df.columns]
    
    # Select and rename columns for the output file
    segment_output_df = segment_df[present_columns].rename(columns=output_columns_map)

    # Generate temporary Excel file
    user_id = update.effective_user.id
    temp_excel_path = excel_manager.create_temp_excel_report(
        segment_output_df, selected_segment_name, f"customer_segment_{selected_segment_name}", DATA_DIR
    )
    
    await update.message.reply_text(f"لیست مشتریان بخش '{selected_segment_name}' در فایل اکسل پیوست شده است: 📄", reply_markup=ReplyKeyboardRemove())
    await send_file_to_user(update, context, temp_excel_path, caption=f"مشتریان بخش {selected_segment_name}")
    
    os.remove(temp_excel_path) # Clean up the temporary file
    logger.info(f"Temporary segment report deleted: {temp_excel_path} ✅")

    return ConversationHandler.END


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

    # Command handler for /new_purchase (now the entry point for mode selection)
    # application.add_handler(CommandHandler("new_purchase", new_purchase_entry_point))

    # ConversationHandler for /new_purchase command 💬
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("new_purchase", new_purchase_entry_point)],
        states={
            SELECT_ENTRY_MODE: [
                MessageHandler(filters.Text("ثبت خرید تکی ➕"), select_single_entry),
                MessageHandler(filters.Text("ثبت چند خرید یکجا 📝"), show_bulk_input_format),
                MessageHandler(filters.Text("انصراف 🛑"), cancel) 
            ],
            SINGLE_CUSTOMER_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_single_customer_name)],
            SINGLE_CUSTOMER_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_single_customer_phone)],
            SINGLE_PURCHASE_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_single_purchase_amount)],
            BULK_PURCHASE_DATA: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_bulk_purchase_data)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],  # Allows user to cancel the conversation 🛑
        allow_reentry=True,  # اجازه ورود چندباره
        per_message=False,   # فقط بر اساس وضعیت فعلی رفتار کن
    )
    application.add_handler(conv_handler)
    
    # ConversationHandler for /analyze_data command 📊
    analyze_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("analyze_data", analyze_data_entry_point)],
        states={
            SELECT_SEGMENT_TYPE: [
                # Match all segment buttons and handle with send_segment_excel
                MessageHandler(filters.Text([
                    "ویژه 🏆", "وفادار ✨", "امید بخش 🌱", "در خطر ⚠️", 
                    "غیر فعال 💤", "از دست رفته 🗑️", "معمولی 🤝", "فاقد تراکنش 🤷",
                    "انصراف 🛑" # Also allow cancel from this state
                ]), send_segment_excel),
            ]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True,
        per_message=False,
    )
    application.add_handler(analyze_conv_handler)
    
    # Existing handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.CONTACT, handle_contact))
    application.add_handler(CommandHandler("list_customers", list_customers))
    application.add_handler(CommandHandler("list_transactions", list_transactions))
    # application.add_handler(CommandHandler("analyze_data", analyze_data))
    application.add_handler(CommandHandler("get_full_excel", get_full_excel))


    # Run the bot until the user presses Ctrl-C 🏃‍♂️
    logger.info("Bot started polling... 🟢")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()

