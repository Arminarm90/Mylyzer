# 📈 ربات تحلیلگر کسب‌وکار تلگرام: دستیار هوشمند شما برای بهبود استراتژی‌های مشتری

این ربات تلگرام یک ابزار قدرتمند برای کسب‌وکارها است که با استفاده از مدل‌های پیشرفته RFM (Recency, Frequency, Monetary) و TAM (Time-based Account Management)، به تحلیل عمیق داده‌های مشتریان و تراکنش‌ها می‌پردازد. با این ربات می‌توانید به راحتی مشتریان ارزشمند، در معرض خطر، غیرفعال و از دست رفته خود را شناسایی کرده و استراتژی‌های بازاریابی خود را بهینه کنید.

## ✨ قابلیت‌های اصلی

* **تحلیل جامع RFM:** مشتریان شما را بر اساس سه معیار اصلی (تازگی خرید، تکرار خرید، و مبلغ خرید) رده‌بندی می‌کند تا ارزشمندترین مشتریان را بشناسید.
* **مدیریت حساب مبتنی بر زمان (TAM):** وضعیت زمانی مشتریان (فعال، در خطر، غیرفعال، از دست رفته، فاقد خرید) را مشخص می‌کند تا بتوانید به سرعت به تغییرات وضعیت آن‌ها واکنش نشان دهید.
* **گزارش‌های اکسل جامع:** خروجی تحلیل‌ها را در قالب یک فایل اکسل کامل و مرتب در اختیار شما قرار می‌دهد.
* **نمودارهای بصری:** نمودارهای دایره‌ای RFM و نمودار میله‌ای TAM را تولید می‌کند تا درک وضعیت مشتریان برای شما آسان‌تر شود.
* **اعلان‌های خودکار:** مشتریان "در خطر" را شناسایی کرده و اعلان‌های دوره‌ای برای شما ارسال می‌کند تا اقدامات لازم را برای حفظ آن‌ها انجام دهید.
* **مدیریت داده آسان:** امکان بارگذاری اطلاعات مشتریان و تراکنش‌ها از طریق فایل‌های اکسل فراهم است.

## 🚀 پیش‌نیازها

برای راه‌اندازی این ربات، شما نیاز به دو چیز اصلی دارید:

1.  **پایتون (Python):** یک زبان برنامه‌نویسی که ربات با آن نوشته شده است. نگران نباشید، نیازی نیست برنامه‌نویسی بلد باشید، فقط باید آن را نصب کنید.
2.  **توکن ربات تلگرام:** یک کد شناسایی منحصر به فرد برای ربات شما در تلگرام.

### ۱. نصب پایتون (Python)

پایتون قلب تپنده این ربات است. برای نصب آن، مراحل زیر را دنبال کنید:

* **دانلود پایتون:**
    به وب‌سایت رسمی پایتون بروید: [https://www.python.org/downloads/](https://www.python.org/downloads/)
    آخرین نسخه پایدار پایتون 3 (به عنوان مثال، Python 3.9 یا بالاتر) را برای سیستم عامل خود (ویندوز، مک، لینوکس) دانلود کنید.

* **نصب پایتون (مخصوص ویندوز):**
    فایل نصبی را که دانلود کرده‌اید، اجرا کنید.
    **بسیار مهم:** در اولین صفحه نصب، **حتماً تیک گزینه `Add Python to PATH` را بزنید.** این کار باعث می‌شود پایتون به درستی در سیستم شما شناسایی شود.
    سپس `Install Now` را انتخاب کنید و منتظر بمانید تا نصب کامل شود.

    * [راهنمای تصویری نصب پایتون در ویندوز (انگلیسی)](https://phoenixnap.com/kb/how-to-install-python-3-windows)
    * [راهنمای نصب پایتون در مک (انگلیسی)](https://www.freecodecamp.org/news/how-to-install-python-on-mac/)

### ۲. دریافت توکن ربات تلگرام

برای اینکه ربات شما در تلگرام فعال شود، نیاز به یک "توکن" دارید. این توکن مانند یک کلید منحصر به فرد برای ربات شماست.

1.  **BotFather را پیدا کنید:**
    در تلگرام خود، `@BotFather` را در قسمت جستجو پیدا کنید و وارد چت با آن شوید.
2.  **شروع به کار با BotFather:**
    دستور `/start` را برای BotFather ارسال کنید.
3.  **ساخت ربات جدید:**
    دستور `/newbot` را ارسال کنید.
4.  **انتخاب نام برای ربات:**
    BotFather از شما یک "نام" برای ربات می‌پرسد. این نام همان چیزی است که کاربران در تلگرام آن را می‌بینند (مثلاً: `تحلیلگر کسب‌وکار من`). یک نام دلخواه انتخاب کنید و ارسال کنید.
5.  **انتخاب نام کاربری (Username) برای ربات:**
    سپس BotFather یک "نام کاربری" برای ربات می‌پرسد. این نام کاربری باید منحصر به فرد باشد و حتماً با `_bot` به پایان برسد (مثلاً: `MyBusinessAnalyzer_bot`). یک نام کاربری مناسب انتخاب کرده و ارسال کنید.
6.  **دریافت توکن:**
    پس از انتخاب نام کاربری، BotFather به شما یک پیام تبریک به همراه "توکن" ربات شما می‌دهد. این توکن یک رشته طولانی از حروف و اعداد است (مثلاً: `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11`).
    **این توکن را کپی کنید و آن را جایی امن نگه دارید. این توکن محرمانه است و نباید با کسی به اشتراک گذاشته شود.**

## 🛠️ راه‌اندازی و نصب پروژه

حالا که پایتون و توکن ربات را دارید، نوبت به آماده‌سازی فایل‌های ربات می‌رسد:

### ۱. دانلود کد پروژه

* به صفحه گیت‌هاب پروژه (همین صفحه) بروید.
* روی دکمه سبز رنگ `Code` کلیک کنید.
* گزینه `Download ZIP` را انتخاب کرده و فایل فشرده پروژه را دانلود کنید.
* فایل ZIP دانلود شده را از حالت فشرده خارج کنید (Extract) و محتویات آن را در یک پوشه مناسب در کامپیوتر خود قرار دهید (مثلاً: `C:\MyBusinessBot`).

### ۲. نصب کتابخانه‌های مورد نیاز

ربات برای کار کردن به چند کتابخانه پایتون دیگر نیاز دارد که باید آن‌ها را نصب کنید.

* **باز کردن ترمینال/Command Prompt:**
    * **در ویندوز:** در پوشه‌ای که فایل‌های پروژه را قرار داده‌اید (مثلاً `C:\MyBusinessBot`)، در نوار آدرس بالای پنجره File Explorer کلیک کنید، عبارت `cmd` را تایپ کرده و Enter بزنید. یک پنجره سیاه رنگ (Command Prompt) باز می‌شود.
    * **در مک/لینوکس:** برنامه Terminal را باز کنید و با استفاده از دستور `cd` به پوشه پروژه بروید. (مثلاً: `cd /path/to/MyBusinessBot`)

* **نصب وابستگی‌ها:**
    در پنجره Command Prompt/Terminal، دستور زیر را تایپ کرده و Enter بزنید:

    ```bash
    pip install -r requirements.txt
    ```
    این دستور تمام کتابخانه‌هایی را که ربات برای اجرا نیاز دارد، به صورت خودکار نصب می‌کند. ممکن است کمی طول بکشد، صبور باشید.

### ۳. تنظیم توکن ربات در فایل `.env`

برای اینکه ربات شما توکن تلگرامش را بشناسد، باید یک فایل تنظیمات ایجاد کنید:

* **ایجاد فایل `.env`:**
    در همان پوشه‌ای که فایل‌های پروژه (مانند `main.py`) قرار دارند، یک فایل جدید با نام `.env` (دقت کنید که نقطه قبل از `env` باشد و هیچ پسوندی نداشته باشد) ایجاد کنید.
    * **در ویندوز:** می‌توانید یک فایل متنی جدید (New Text Document) بسازید، سپس نام آن را به `.env` تغییر دهید. ممکن است ویندوز هشدار دهد که تغییر پسوند باعث غیرقابل استفاده شدن فایل می‌شود، تأیید کنید.
    * **در مک/لینوکس:** می‌توانید از طریق Terminal با دستور `touch .env` این فایل را ایجاد کنید.

* **اضافه کردن توکن به `.env`:**
    فایل `.env` را با یک ویرایشگر متن ساده (مانند Notepad در ویندوز یا TextEdit در مک) باز کنید و خط زیر را داخل آن بنویسید:

    ```
    BOT_TOKEN=YOUR_TELEGRAM_BOT_TOKEN_HERE
    ```
    **به جای `YOUR_TELEGRAM_BOT_TOKEN_HERE`، توکنی که از BotFather گرفتید را قرار دهید.**
    مثال:
    ```
    BOT_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
    ```
    فایل را ذخیره و ببندید.

### ۴. اضافه کردن فونت فارسی

برای نمایش صحیح نمودارها و متن‌های فارسی، ربات نیاز به یک فونت فارسی دارد:

* **ساخت پوشه `fonts`:**
    در کنار فایل `main.py`، یک پوشه جدید به نام `fonts` (با حروف کوچک) ایجاد کنید.
* **دانلود و قرار دادن فونت:**
    فایل فونت `Iranian-Sans.ttf` را دانلود کنید و در این پوشه `fonts` قرار دهید. می‌توانید این فونت را از منابع معتبر دانلود کنید یا از لینک زیر استفاده کنید:
    [دانلود فونت Iranian-Sans.ttf (نمونه لینک، در صورت نیاز جایگزین شود)](https://rastikerdar.github.io/vazirmatn/fonts/webfonts/Vazirmatn-Regular.ttf) - (توجه: این یک نمونه لینک است. در صورت نیاز به فونت `Iranian-Sans.ttf` واقعی، باید آن را در ریپازیتوری خود قرار دهید یا لینک دانلود مستقیم آن را اینجا بگذارید.)
    **توجه:** اگر فایل فونت شما نام دیگری دارد، مطمئن شوید که در کد `chart_utils.py` مسیر `font_path` را به نام صحیح تغییر دهید، یا نام فایل را به `Iranian-Sans.ttf` تغییر دهید.

## ▶️ نحوه اجرای ربات

پس از انجام تمام مراحل بالا، اکنون آماده‌اید تا ربات را اجرا کنید:

* دوباره به پنجره Command Prompt/Terminal که در مرحله "نصب کتابخانه‌ها" باز کرده بودید برگردید (یا اگر بسته شده، دوباره آن را در پوشه پروژه باز کنید).
* دستور زیر را تایپ کرده و Enter بزنید:

    ```bash
    python main.py
    ```
* اگر همه چیز به درستی انجام شده باشد، خواهید دید که ربات شروع به کار می‌کند و پیام‌هایی مشابه "Bot started polling..." را مشاهده خواهید کرد.

**تبریک می‌گویم! ربات شما اکنون فعال و آماده استفاده است.**

## 🤖 استفاده از ربات در تلگرام

حالا می‌توانید به تلگرام خود بروید و با ربات تعامل داشته باشید:

1.  **پیدا کردن ربات:**
    نام کاربری ربات خود را که هنگام ساخت با BotFather انتخاب کردید (مثلاً `MyBusinessAnalyzer_bot`) در جستجوی تلگرام وارد کنید و ربات خود را پیدا کنید.
2.  **شروع به کار:**
    روی ربات کلیک کرده و دکمه `Start` را بزنید، یا دستور `/start` را برای ربات ارسال کنید.
3.  **اشتراک‌گذاری شماره تماس:**
    ربات از شما می‌خواهد که شماره تلفن خود را به اشتراک بگذارید. این کار برای شناسایی شما به عنوان کاربر مجاز و مدیریت داده‌هایتان لازم است. روی دکمه "Share Contact" یا مشابه آن کلیک کنید.
4.  **آپلود فایل اکسل داده‌ها:**
    برای اینکه ربات بتواند تحلیل را انجام دهد، به داده‌های شما نیاز دارد. شما باید یک فایل اکسل حاوی اطلاعات مشتریان و تراکنش‌های خود را برای ربات ارسال کنید.
    * **فرمت فایل اکسل:**
        فایل اکسل شما باید شامل دو شیت (Sheet) با نام‌های دقیق زیر باشد:
        * **شیت `Customers` (مشتریان):** شامل اطلاعات مشتریان شما با سربرگ‌های دقیق:
            * `کد مشتری` (CustomerID)
            * `نام` (Name)
            * `شماره تماس` (Phone Number)
            * `تاریخ عضویت` (Membership Date)
            * `توضیحات` (Description)
        * **شیت `Transactions` (تراکنش‌ها):** شامل جزئیات تراکنش‌ها با سربرگ‌های دقیق:
            * `شناسه مشتری` (CustomerID)
            * `تاریخ فاکتور` (Invoice Date) - **فرمت تاریخ باید `YYYY-MM-DD` شمسی باشد، مانند `1403-03-25`**
            * `شماره فاکتور` (Invoice Number)
            * `مبلغ (تومان)` (Amount in Toman)
    * **نحوه ارسال:** فایل اکسل خود را به عنوان یک `Document` (نه عکس) برای ربات بفرستید.
    * **نمونه فایل اکسل:**
        برای اینکه مطمئن شوید فرمت فایل شما صحیح است، می‌توانید یک فایل اکسل نمونه با فرمت صحیح را از لینک زیر دانلود کنید:
        [لینک دانلود Sample_Data.xlsx](https://github.com/YOUR_USERNAME/YOUR_REPO_NAME/raw/main/Sample_Data.xlsx)
        *(به جای `YOUR_USERNAME` و `YOUR_REPO_NAME`، نام کاربری و نام ریپازیتوری خود در گیت‌هاب را قرار دهید تا لینک مستقیم به فایل نمونه در پروژه شما باشد.)*

5.  **دستورات ربات:**
    پس از آپلود موفقیت‌آمیز فایل اکسل، می‌توانید از دستورات زیر برای تعامل با ربات استفاده کنید:

    * `/analyze_data`: (پس از آپلود فایل اکسل) این دستور داده‌های شما را تحلیل کرده و گزارش‌های RFM و TAM را تولید می‌کند.
    * `/list_customers`: لیست مشتریان ذخیره شده را نمایش می‌دهد.
    * `/list_transactions`: لیست تراکنش‌های ذخیره شده را نمایش می‌دهد.
    * `/get_full_excel`: یک فایل اکسل کامل شامل تحلیل RFM و TAM را برای شما ارسال می‌کند.
    * `/import_transactions`: برای بارگذاری تراکنش‌های جدید به صورت جداگانه (بدون نیاز به آپلود مجدد اطلاعات مشتریان).
    * `/cancel`: برای لغو هر فرآیند در حال انجام.

## ⚠️ هشدارها و نکات مهم

* **خطای `python is not recognized...`:** اگر هنگام اجرای `python main.py` این خطا را دریافت کردید، به احتمال زیاد هنگام نصب پایتون گزینه `Add Python to PATH` را تیک نزده‌اید. باید پایتون را مجدداً نصب کنید و مطمئن شوید که این گزینه را فعال می‌کنید.
* **مشکل در نصب کتابخانه‌ها:** اگر `pip install -r requirements.txt` با خطا مواجه شد، مطمئن شوید که اتصال اینترنت شما برقرار است و فایروال یا آنتی‌ویروس شما مانع نصب نمی‌شود.
* **فرمت فایل اکسل:** صحت فرمت شیت‌ها و سربرگ‌های فایل اکسل شما بسیار مهم است. حتی یک غلط املایی کوچک می‌تواند باعث خطا شود. از فایل نمونه ارائه شده برای الگوبرداری استفاده کنید.
* **توکن ربات:** توکن ربات تلگرام خود را محرمانه نگه دارید و هرگز آن را در کد یا جاهای عمومی منتشر نکنید.
* **داده‌های کاربران:** ربات داده‌های شما را در پوشه‌ای به نام `user_data` در کنار فایل‌های پروژه ذخیره می‌کند. این پوشه شامل فایل‌های اکسل شما و لاگ‌های مربوط به اعلان‌هاست. از این پوشه مراقبت کنید و آن را حذف نکنید.

## ❓ سوالات متداول (FAQ)

* **آیا می‌توانم از ربات برای چندین کسب‌وکار استفاده کنم؟**
    بله، ربات برای هر کاربر به صورت جداگانه داده‌ها را مدیریت می‌کند. هر کاربر (شما) می‌تواند فایل‌های اکسل کسب‌وکار خود را آپلود کند.
* **اطلاعات من کجا ذخیره می‌شود؟**
    داده‌های مشتریان و تراکنش‌های شما در فایل‌های اکسل مربوط به شما، در پوشه `user_data` در همان محلی که ربات را اجرا کرده‌اید، ذخیره می‌شوند.
* **آیا ربات همیشه باید روشن باشد؟**
    بله، برای اینکه ربات به پیام‌های تلگرام شما پاسخ دهد و اعلان‌های خودکار را ارسال کند، برنامه `main.py` باید در حال اجرا باشد. اگر پنجره Command Prompt/Terminal را ببندید، ربات متوقف می‌شود.

## 🤝 مشارکت (Contribution)

اگر به توسعه این پروژه علاقه دارید، می‌توانید:

* Issues/Bug Reports: مشکلات یا باگ‌ها را گزارش دهید.
* Feature Requests: قابلیت‌های جدید پیشنهاد دهید.
* Pull Requests: کدهای خود را برای بهبود پروژه ارسال کنید.

## 📄 مجوز (License)

این پروژه تحت مجوز MIT منتشر شده است. برای جزئیات بیشتر، فایل `LICENSE` را ببینید.