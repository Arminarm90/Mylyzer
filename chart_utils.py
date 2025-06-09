import matplotlib.pyplot as plt
import io
import os
from matplotlib import font_manager
import arabic_reshaper
from bidi.algorithm import get_display


# Pie chart
# فونت فارسی
font_path = "./fonts/Iranian-Sans.ttf"
font_prop = font_manager.FontProperties(fname=font_path)

def reshape_farsi(text):
    reshaped = arabic_reshaper.reshape(text)  # اصلاح اتصال حروف
    return get_display(reshaped)              # راست‌چین‌سازی متن

def create_rfm_pie_chart(df_segmented):
    counts = df_segmented["دسته رفتاری نهایی"].value_counts()
    labels = [reshape_farsi(label) for label in counts.index.tolist()]
    sizes = counts.values.tolist()

    fig, ax = plt.subplots(figsize=(7, 7))
    ax.pie(
        sizes,
        labels=labels,
        autopct='%1.1f%%',
        startangle=120,
        textprops={'fontproperties': font_prop}
    )
    ax.axis('equal')
    plt.title(reshape_farsi("درصد دسته‌های رفتاری مشتریان"), fontproperties=font_prop, fontsize=14)

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close()
    return buf


# Bar chart
def reshape_farsi(text):
    reshaped = arabic_reshaper.reshape(text)
    return get_display(reshaped)

def create_tam_bar_chart(df_segmented):
    counts = df_segmented["وضعیت زمانی"].value_counts()
    statuses = counts.index.tolist()
    values = counts.values.tolist()

    label_map = {
        "Active": "فعال",
        "At Risk": "در خطر",
        "Inactive": "غیرفعال",
        "Lost": "از دست رفته",
        "No Purchase": "فاقد خرید"
    }

    labels_fa = [reshape_farsi(label_map.get(st, st)) for st in statuses]

    # 🎨 رنگ‌ها به ترتیب وضعیت‌ها
    color_map = {
        "Active": "#4CAF50",       # سبز
        "At Risk": "#FFC107",      # زرد
        "Inactive": "#9E9E9E",     # خاکستری
        "Lost": "#F44336",         # قرمز
        "No Purchase": "#607D8B"   # آبی خاکستری
    }

    bar_colors = [color_map.get(st, "#888") for st in statuses]

    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(labels_fa, values, color=bar_colors)

    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2, height + 0.5, f'{int(height)}',
                ha='center', va='bottom', fontproperties=font_prop, fontsize=10)

    ax.set_title(reshape_farsi("تعداد مشتریان در وضعیت‌های زمانی"), fontproperties=font_prop, fontsize=14)
    ax.set_ylabel(reshape_farsi("تعداد"), fontproperties=font_prop)
    ax.set_xlabel(reshape_farsi("وضعیت زمانی"), fontproperties=font_prop)

    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close()
    return buf
