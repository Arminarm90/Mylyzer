# data_analyzer.py
import pandas as pd
from datetime import datetime
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import warnings
import logging # Import logging module 📝
import jdatetime

# Setup a logger for this module
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO) # Set logging level for this module

# Suppress KMeans warning for n_init in older scikit-learn versions 🤫
warnings.filterwarnings("ignore", category=UserWarning, module="sklearn.cluster._kmeans")

def calculate_rfm(df_transactions):
    """
    Calculates RFM (Recency, Frequency, Monetary) values for each customer
    based on their transaction data. 📊

    Args:
        df_transactions (pd.DataFrame): DataFrame containing transaction data
                                       با ستون‌های 'شناسه مشتری', 'تاریخ فاکتور', 'مبلغ (تومان)'. 📈

    Returns:
        pd.DataFrame: A DataFrame with 'شناسه مشتری', 'Recency', 'Frequency', 'Monetary' columns.
                      Returns an empty DataFrame if input is empty or dates are invalid. 🚫
    """
    if df_transactions.empty:
        return pd.DataFrame()

    # Convert 'تاریخ فاکتور' to datetime objects directly using pandas.to_datetime.
    # This is robust for various standard Gregorian date formats.
    # 'errors='coerce' will turn any unparseable dates into NaT (Not a Time).
    def convert_shamsi_to_gregorian(shamsi_str):
        try:
            y, m, d = map(int, str(shamsi_str).split('-'))
            return jdatetime.date(y, m, d).togregorian()
        except:
            return pd.NaT

    df_transactions['تاریخ فاکتور_greg'] = df_transactions['تاریخ فاکتور'].apply(convert_shamsi_to_gregorian)

    
    # Drop rows where date conversion resulted in NaT (Not a Time)
    df_transactions.dropna(subset=['تاریخ فاکتور_greg'], inplace=True) 

    if df_transactions['تاریخ فاکتور_greg'].empty:
        return pd.DataFrame() # No valid transactions to calculate RFM 🤷‍♂️

    # Define a snapshot date as the day after the last transaction date (Gregorian) 🗓️
    # This ensures Recency is calculated correctly for the most recent purchase
    snapshot_date = df_transactions['تاریخ فاکتور_greg'].max() + pd.Timedelta(days=1)
    
    # Calculate RFM components ➕
    rfm_df = df_transactions.groupby('شناسه مشتری').agg(
        Recency=('تاریخ فاکتور_greg', lambda date: (snapshot_date - date.max()).days), # Days since last purchase ⏰
        Frequency=('شماره فاکتور', 'count'), # Count of transactions 🔢
        Monetary=('مبلغ (تومان)', 'sum') # Total spending 💲
    ).reset_index()

    return rfm_df

def segment_customers_kmeans(rfm_df, n_clusters=3):
    """
    Segments customers into clusters using KMeans algorithm based on their RFM values. 🧑‍🤝‍🧑
    Standardizes RFM features before clustering. 📏

    Args:
        rfm_df (pd.DataFrame): DataFrame with 'شناسه مشتری', 'Recency', 'Frequency', 'Monetary'. 📊
        n_clusters (int): The number of clusters to form. 🔢

    Returns:
        pd.DataFrame: The input rfm_df with an additional 'Segment' column indicating the cluster. 🏷️
                      Returns the original rfm_df if clustering cannot be performed (e.g., not enough data). 🚫
    """
    if rfm_df.empty:
        return rfm_df

    # Features for clustering 🧩
    X = rfm_df[['Recency', 'Frequency', 'Monetary']]

    # Handle cases where n_clusters is greater than the number of samples ⚠️
    if len(X) < n_clusters:
        # Adjust n_clusters to be at most the number of samples ⬇️
        n_clusters = len(X)
        if n_clusters == 0:
            return rfm_df # No data to cluster 🤷‍♀️
        if n_clusters < 2:
            # If only one or zero samples, clustering is trivial or impossible 🛑
            rfm_df['Segment'] = 0 # Assign all to segment 0 (single cluster) 🎯
            return rfm_df

    # Standardize the RFM features. This is crucial for KMeans as it's distance-based. 📏
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Apply KMeans clustering 🧠
    # n_init='auto' handles the warning for explicit initialization in newer scikit-learn versions
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init='auto')
    rfm_df['Segment'] = kmeans.fit_predict(X_scaled) # Predict on scaled data ✅

    return rfm_df

def perform_analysis(df_transactions, df_customers): # Added df_customers parameter
    """
    Performs comprehensive customer analysis using RFM and KMeans clustering. 📊
    Generates a human-readable report summarizing customer segments and overall insights. 📝

    Args:
        df_transactions (pd.DataFrame): DataFrame containing transaction data. 📈
        df_customers (pd.DataFrame): DataFrame containing customer data (for names). 🧑‍🤝‍🧑

    Returns:
        str: A formatted string containing the analysis report. 📄
    """
    rfm_df = calculate_rfm(df_transactions)

    if rfm_df.empty:
        return "داده کافی برای انجام تحلیل RFM وجود ندارد. 😔"

    # Segment customers into 3 clusters (you can adjust n_clusters based on your data) 🧩
    segmented_rfm = segment_customers_kmeans(rfm_df, n_clusters=3)

    if segmented_rfm.empty:
        return "امکان خوشه‌بندی مشتریان وجود نداشت. 🚫"

    report_content = "--- گزارش تحلیل مشتریان 📊 ---\n\n"

    # Analyze and describe each segment
    # Sort segments by their average Monetary value in descending order 💰
    segment_summary = segmented_rfm.groupby('Segment').agg(
        Avg_Recency=('Recency', 'mean'),
        Avg_Frequency=('Frequency', 'mean'),
        Avg_Monetary=('Monetary', 'mean'),
        Num_Customers=('شناسه مشتری', 'count')
    ).sort_values(by='Avg_Monetary', ascending=False).reset_index()

    # Define descriptive labels for segments based on their sorted order (by Monetary value)
    # These labels provide more meaningful context to the user.
    descriptive_labels = [
        "بخش مشتریان باارزش (قهرمانان 🏆)",
        "بخش مشتریان فعال (با پتانسیل رشد 🌱)",
        "بخش مشتریان نیازمند توجه (در معرض خطر ⚠️)"
    ]
    
    # Handle cases where fewer than 3 clusters are formed
    if len(segment_summary) < len(descriptive_labels):
        # Adjust labels if fewer clusters are present
        adjusted_labels = descriptive_labels[:len(segment_summary)]
    else:
        adjusted_labels = descriptive_labels

    # Merge segmented_rfm with df_customers to get customer names
    # Ensure 'شناسه مشتری' in segmented_rfm corresponds to 'کد مشتری' in df_customers
    # Using 'left' merge to keep all customers from segmented_rfm
    segmented_rfm_with_names = pd.merge(
        segmented_rfm,
        df_customers[['کد مشتری', 'نام']],
        left_on='شناسه مشتری',
        right_on='کد مشتری',
        how='left'
    )

    # Group by segment and collect customer names for each segment
    # Using .unique() to avoid duplicate names if a customer appears multiple times in a segment (though unlikely with RFM)
    segment_customer_names = segmented_rfm_with_names.groupby('Segment')['نام'].apply(lambda x: list(x.unique())).to_dict()


    for index, row in segment_summary.iterrows():
        segment_id = int(row['Segment'])
        avg_recency = row['Avg_Recency']
        avg_frequency = row['Avg_Frequency']
        avg_monetary = row['Avg_Monetary']
        num_customers = row['Num_Customers']
        
        # Assign a more descriptive label based on the sorted order (index)
        current_segment_label = adjusted_labels[index] if index < len(adjusted_labels) else f"بخش {segment_id + 1}"

        report_content += f"{current_segment_label} (تعداد مشتریان: {num_customers}):\n"
        
        # Get customer names for this specific segment
        customers_in_this_segment = segment_customer_names.get(segment_id, [])
        if customers_in_this_segment:
            customer_names_str = ", ".join(customers_in_this_segment)
            report_content += f"  مشتریان در این بخش: {customer_names_str}\n" # New line for customer names
        else:
            report_content += "  مشتریانی در این بخش یافت نشدند. 🤷\n"
        
        report_content += f"  میانگین تازگی (روز از آخرین خرید): {avg_recency:.0f} روز ⏰\n"
        report_content += f"  میانگین تکرار (تعداد خرید): {avg_frequency:.1f}\n"
        report_content += f"  میانگین ارزش پولی (کل هزینه): {avg_monetary:,.0f} تومان 💲\n"
        
        # Provide interpretations based on the assigned label and general RFM characteristics
        if "باارزش" in current_segment_label:
            report_content += "  این مشتریان اخیراً زیاد خرید کرده‌اند، اغلب تکرار خرید دارند و بیشترین هزینه را انجام داده‌اند. حفظ این مشتریان برای کسب‌وکار شما حیاتی است. 💎\n"
        elif "فعال" in current_segment_label:
            report_content += "  این مشتریان نسبتاً فعال هستند و پتانسیل بالایی برای تبدیل شدن به مشتریان باارزش دارند. آن‌ها را با پیشنهادهای جذاب تشویق به خریدهای بیشتر کنید. ✨\n"
        elif "نیازمند توجه" in current_segment_label:
            report_content += "  این مشتریان مدتی است که خرید نکرده‌اند یا کمتر فعال بوده‌اند. ممکن است در معرض خطر ریزش باشند. برای بازگرداندن آن‌ها، استراتژی‌های خاصی (مانند تخفیف یا یادآوری) را در نظر بگیرید. 🔙\n"
        else:
            report_content += "  این بخش ویژگی‌های خاصی دارد که نیاز به بررسی بیشتر دارد. 🤔\n"
        
        report_content += "\n"

    # Overall summary 📈
    total_customers_analyzed = len(rfm_df)
    total_transactions_processed = len(df_transactions)
    total_sales_volume = df_transactions['مبلغ (تومان)'].sum()
    
    report_content += f"--- خلاصه کلی 📊 ---\n"
    report_content += f"تعداد کل مشتریان تحلیل شده: {total_customers_analyzed} 🧑‍🤝‍🧑\n"
    report_content += f"تعداد کل تراکنش‌های پردازش شده: {total_transactions_processed} �\n"
    report_content += f"حجم کل فروش: {total_sales_volume:,.0f} تومان 💰\n"
    report_content += "\nاین تحلیل به شما کمک می‌کند تا استراتژی‌های بازاریابی و فروش خود را هدفمندتر کنید. ✨"

    return report_content