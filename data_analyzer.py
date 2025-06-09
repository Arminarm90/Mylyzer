# data_analyzer.py
import pandas as pd
from datetime import datetime
import jdatetime # Import jdatetime for Shamsi date conversion 📝
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import warnings
import logging # Import logging module 📝

# Setup a logger for this module
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO) # Set logging level for this module

# Suppress KMeans warning for n_init in older scikit-learn versions 🤫
warnings.filterwarnings("ignore", category=UserWarning, module="sklearn.cluster._kmeans")

def convert_shamsi_to_gregorian(shamsi_date_str):
    """
    Converts a Shamsi date string (e.g., '1404-03-17') to a Gregorian datetime object.
    Handles potential parsing errors by returning NaT.
    """
    if pd.isna(shamsi_date_str) or not isinstance(shamsi_date_str, str):
        return pd.NaT # Return Not a Time for NaN or non-string inputs
    try:
        # Assuming format 'YYYY-MM-DD' for Shamsi date string
        # jdatetime.date(year, month, day)
        parts = shamsi_date_str.split('-')
        j_year, j_month, j_day = int(parts[0]), int(parts[1]), int(parts[2])
        g_date = jdatetime.date(j_year, j_month, j_day).togregorian()
        return datetime(g_date.year, g_date.month, g_date.day)
    except Exception as e:
        logger.warning(f"Failed to convert Shamsi date '{shamsi_date_str}' to Gregorian: {e}")
        return pd.NaT # Return Not a Time if conversion fails

def convert_gregorian_to_shamsi_str(gregorian_date_obj):
    """
    Converts a Gregorian datetime object to a Shamsi date string (YYYY-MM-DD).
    Handles NaT values by returning 'N/A'.
    """
    if pd.isna(gregorian_date_obj):
        return 'N/A'
    try:
        j_date = jdatetime.date.fromgregorian(gregorian_date_obj.year, gregorian_date_obj.month, gregorian_date_obj.day)
        return j_date.strftime("%Y-%m-%d")
    except Exception as e:
        logger.warning(f"Failed to convert Gregorian date '{gregorian_date_obj}' to Shamsi: {e}")
        return 'N/A'


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
        logger.info("df_transactions is empty in calculate_rfm.")
        return pd.DataFrame()

    # Convert 'تاریخ فاکتور' (Shamsi) to Gregorian datetime objects 🗓️
    df_transactions['تاریخ فاکتور_greg'] = df_transactions['تاریخ فاکتور'].apply(convert_shamsi_to_gregorian)

    # Drop rows where date conversion resulted in NaT (Not a Time)
    df_transactions.dropna(subset=['تاریخ فاکتور_greg'], inplace=True) 

    if df_transactions['تاریخ فاکتور_greg'].empty:
        logger.info("After Shamsi date cleaning, df_transactions['تاریخ فاکتور_greg'] is empty. No valid transactions for RFM.")
        return pd.DataFrame() # No valid transactions to calculate RFM 🤷‍♂️

    # Define a snapshot date as the day after the last transaction date (Gregorian) 🗓️
    snapshot_date = df_transactions['تاریخ فاکتور_greg'].max() + pd.Timedelta(days=1)
    
    # Calculate RFM components ➕
    rfm_df = df_transactions.groupby('شناسه مشتری').agg(
        Recency=('تاریخ فاکتور_greg', lambda date: (snapshot_date - date.max()).days), # Days since last purchase ⏰
        Frequency=('شماره فاکتور', 'count'), # Count of transactions 🔢
        Monetary=('مبلغ (تومان)', 'sum') # Total spending 💲
    ).reset_index()

    # Rename 'شناسه مشتری' to 'CustomerID' for consistency with RFM definitions
    rfm_df.rename(columns={'شناسه مشتری': 'CustomerID'}, inplace=True)
    logger.info(f"RFM Calculated DataFrame (first 5 rows):\n{rfm_df.head().to_string()}")
    return rfm_df

def calculate_rfm_scores(rfm_df):
    """
    Calculates R, F, M scores (1-5) based on RFM values using quintiles. 
    Higher Recency = lower R score (inverse). Higher Frequency/Monetary = higher F/M score.
    """
    if rfm_df.empty:
        logger.info("rfm_df is empty in calculate_rfm_scores.")
        return rfm_df

    for col_name, score_col_name, is_recency in [('Recency', 'R_Score', True), 
                                                 ('Frequency', 'F_Score', False), 
                                                 ('Monetary', 'M_Score', False)]:
        
        # Ensure the column is numeric before checking unique values
        if not pd.api.types.is_numeric_dtype(rfm_df[col_name]):
            logger.warning(f"Column '{col_name}' is NOT numeric. Type: {rfm_df[col_name].dtype}. Skipping scoring for this column.")
            rfm_df[score_col_name] = 0 # Assign a default score if not numeric
            continue
        
        num_unique_values = rfm_df[col_name].nunique()
        
        # Handle cases with very few unique values to avoid qcut errors
        if num_unique_values == 0:
            rfm_df[score_col_name] = 0 # No data, assign 0
            logger.info(f"Column '{col_name}' has 0 unique values. Assigned score 0.")
        elif num_unique_values == 1:
            if is_recency:
                # If only one Recency value, and it's very recent, give high score
                rfm_df[score_col_name] = 5 if rfm_df[col_name].iloc[0] <= 30 else 1 
                logger.info(f"Column '{col_name}' has 1 unique value. Assigned R_Score based on heuristic.")
            else:
                rfm_df[score_col_name] = 3 # Assign mid-score for F/M if no variance
                logger.info(f"Column '{col_name}' has 1 unique value. Assigned {col_name[0]}_Score=3.")
        else:
            # For 2 to 5 unique values, use num_unique_values as n_bins to avoid errors
            # For > 5 unique values, use 5 bins
            n_bins = min(5, num_unique_values)
            
            # Labels for qcut: Recency is inverse, F/M are direct
            if is_recency:
                labels = range(n_bins, 0, -1) # e.g., [5,4,3,2,1] for 5 bins
            else:
                labels = range(1, n_bins + 1) # e.g., [1,2,3,4,5] for 5 bins
            
            try:
                # Ensure labels length matches n_bins
                rfm_df[score_col_name] = pd.qcut(rfm_df[col_name], n_bins, labels=list(labels), duplicates='drop')
                logger.info(f"Assigned {score_col_name} via qcut with {n_bins} bins.")
            except Exception as e:
                logger.error(f"Error in pd.qcut for column '{col_name}' with {n_bins} bins: {e}. Assigning default score.")
                if is_recency:
                    rfm_df[score_col_name] = 5 if rfm_df[col_name].iloc[0] <= 30 else 1
                else:
                    rfm_df[score_col_name] = 3
        
    # Convert to int for cleaner display, handling potential non-numeric values gracefully
    for score_col in ['R_Score', 'F_Score', 'M_Score']:
        # Ensure the column exists before converting, default to 0 if not
        if score_col not in rfm_df.columns:
            logger.warning(f"Score column '{score_col}' was NOT created. Defaulting to 0.")
            rfm_df[score_col] = 0 
        else:
            logger.info(f"Score column '{score_col}' found. Type: {rfm_df[score_col].dtype}")
        rfm_df[score_col] = rfm_df[score_col].astype(int)

    logger.info(f"RFM Scored DataFrame (final first 5 rows):\n{rfm_df.head().to_string()}")
    return rfm_df

def determine_tam_status(recency_days):
    """
    Determines the TAM (Temporal Activity Model) status based on Recency in days.
    """
    if recency_days <= 30:
        return 'Active'
    elif recency_days <= 90:
        return 'At Risk'
    elif recency_days <= 180:
        return 'Inactive'
    else:
        return 'Lost'

def assign_segment(row):
    """
    Assigns the final customer segment based on RFM scores and TAM status.
    """
    R, F, M = row['R_Score'], row['F_Score'], row['M_Score']
    tam_status = row['TAM_Status']

    if R >= 4 and F >= 4 and M >= 4 and tam_status == 'Active':
        return "ویژه" # Special/Champion
    elif R == 5 and F >= 3 and tam_status == 'Active':
        return "وفادار" # Loyal
    elif R >= 4 and F <= 2 and tam_status == 'Active':
        return "امید بخش" # Promising
    elif tam_status == 'At Risk' and (F >= 3 or M >= 3):
        return "در خطر" # At Risk
    elif tam_status == 'Inactive':
        return "غیر فعال" # Inactive
    elif tam_status == 'Lost' and F == 1 and M == 1:
        return "از دست رفته" # Lost
    else:
        return "معمولی" # Regular/Normal

def get_full_customer_segments_df(df_transactions, df_customers):
    """
    Performs comprehensive customer segmentation using RFM and TAM models.
    Returns a DataFrame with each customer's details and their assigned segment.
    """
    # Keep a copy of original df_customers to retrieve original 'تاریخ عضویت' later
    df_customers_original = df_customers.copy()

    # Ensure 'تاریخ عضویت' in df_customers_original is treated as string for the final output
    df_customers_original['تاریخ عضویت'] = df_customers_original['تاریخ عضویت'].astype(str)

    rfm_df = calculate_rfm(df_transactions)
    
    if rfm_df.empty:
        logger.warning("RFM DataFrame is empty after calculation. All customers will be 'فاقد تراکنش'.")
        final_df_no_transactions = df_customers_original.copy() # Use original customer data
        final_df_no_transactions['روز از آخرین خرید'] = -1 # Indicates no recent purchase
        final_df_no_transactions['تعداد خرید'] = 0
        final_df_no_transactions['مجموع خرید'] = 0
        final_df_no_transactions['امتیاز تازگی'] = 0
        final_df_no_transactions['امتیاز تکرار'] = 0
        final_df_no_transactions['امتیاز مبلغ'] = 0
        final_df_no_transactions['وضعیت زمانی'] = 'No Purchase'
        final_df_no_transactions['دسته رفتاری نهایی'] = 'فاقد تراکنش'
        final_df_no_transactions['آخرین خرید'] = 'N/A' # Keep as N/A if no transactions

        final_df_no_transactions.rename(columns={'نام': 'نام مشتری'}, inplace=True)
        
        desired_order_no_txn = [
            'کد مشتری', 'نام مشتری', 'شماره تماس', 'تاریخ عضویت', 'توضیحات',
            'آخرین خرید', 'تعداد خرید', 'مجموع خرید', 'روز از آخرین خرید',
            'امتیاز تازگی', 'امتیاز تکرار', 'امتیاز مبلغ', 'وضعیت زمانی', 'دسته رفتاری نهایی'
        ]
        final_df_no_transactions = final_df_no_transactions[[col for col in desired_order_no_txn if col in final_df_no_transactions.columns]]

        logger.info(f"Full Segmented DataFrame (all 'فاقد تراکنش' due to no transactions):\n{final_df_no_transactions.head().to_string()}")
        logger.info(f"Segment Distribution:\n{final_df_no_transactions['دسته رفتاری نهایی'].value_counts().to_string()}")
        return final_df_no_transactions


    rfm_df_scored = calculate_rfm_scores(rfm_df)
    if rfm_df_scored.empty:
        logger.warning("RFM Scored DataFrame is empty after scoring.")
        return pd.DataFrame() # Should not happen if rfm_df is not empty

    rfm_df_scored['TAM_Status'] = rfm_df_scored['Recency'].apply(determine_tam_status)
    rfm_df_scored['Segment'] = rfm_df_scored.apply(assign_segment, axis=1)

    # Calculate LastPurchase as Gregorian datetime object for merging/consistency
    today = datetime.now()
    rfm_df_scored['آخرین خرید_greg'] = rfm_df_scored['Recency'].apply(lambda x: (today - pd.Timedelta(days=x)))

    # Merge with original customer details to retain original 'تاریخ عضویت'
    final_df = pd.merge(
        df_customers_original, # Merge with the original customer data
        rfm_df_scored[[
            'CustomerID', 'Recency', 'Frequency', 'Monetary',
            'R_Score', 'F_Score', 'M_Score', 'TAM_Status', 'Segment',
            'آخرین خرید_greg' # Now contains Gregorian datetime objects
        ]],
        left_on='کد مشتری',
        right_on='CustomerID',
        how='left'
    )

    # Fill NaN values for customers who might not have transactions
    final_df['Recency'].fillna(-1, inplace=True) 
    final_df['Frequency'].fillna(0, inplace=True)
    final_df['Monetary'].fillna(0, inplace=True)
    final_df['R_Score'].fillna(0, inplace=True)
    final_df['F_Score'].fillna(0, inplace=True)
    final_df['M_Score'].fillna(0, inplace=True)
    final_df['TAM_Status'].fillna('No Purchase', inplace=True) 
    final_df['Segment'].fillna('فاقد تراکنش', inplace=True)
    final_df['آخرین خرید_greg'].fillna(pd.NaT, inplace=True) # Fill with NaT for consistency before Shamsi conversion

    # Convert 'آخرین خرید_greg' to Shamsi string for final output
    final_df['آخرین خرید'] = final_df['آخرین خرید_greg'].apply(convert_gregorian_to_shamsi_str)
    final_df.drop(columns=['آخرین خرید_greg'], inplace=True) # Drop the temporary Gregorian column

    # Drop the redundant 'CustomerID' column from merge
    if 'CustomerID' in final_df.columns:
        final_df.drop(columns=['CustomerID'], inplace=True)

    # Rename 'نام' to 'نام مشتری' for consistency with output format
    final_df.rename(columns={
        'نام': 'نام مشتری',
        'Recency': 'روز از آخرین خرید',
        'Frequency': 'تعداد خرید',
        'Monetary': 'مجموع خرید',
        'R_Score': 'امتیاز تازگی',
        'F_Score': 'امتیاز تکرار',
        'M_Score': 'امتیاز مبلغ',
        'TAM_Status': 'وضعیت زمانی',
        'Segment': 'دسته رفتاری نهایی'
    }, inplace=True)
    
    # Ensure column order matches the desired output from RFM + TAM.pdf
    desired_order = [
        'کد مشتری', 'نام مشتری', 'شماره تماس', 'تاریخ عضویت', 'توضیحات', # Original customer details
        'آخرین خرید', 'تعداد خرید', 'مجموع خرید', # Summary RFM
        'روز از آخرین خرید', 'امتیاز تازگی', 'امتیاز تکرار', 'امتیاز مبلغ', # Detailed RFM
        'وضعیت زمانی', 'دسته رفتاری نهایی' # TAM and Segment
    ]
    final_df = final_df[[col for col in desired_order if col in final_df.columns]]


    logger.info(f"Full Segmented DataFrame (first 5 rows with scores and segment):\n{final_df.head().to_string()}")
    logger.info(f"Segment Distribution:\n{final_df['دسته رفتاری نهایی'].value_counts().to_string()}")

    return final_df

