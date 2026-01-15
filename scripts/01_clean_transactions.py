"""
01_clean_transactions.py
Cleans raw transaction data and prepares for Power BI import.

Author: Jason Donner
Date: 15-01-2026
"""

import pandas as pd
from pathlib import Path
from datetime import datetime

# Configuration
RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")
ANCHOR_DATE = "2024-01-01"  # Arbitrary start date for relative days

def load_transactions():
    """Load raw transaction data with optimized dtypes."""
    print("Loading transactions...")
    
    dtype_spec = {
        'household_key': 'int32',
        'BASKET_ID': 'int64',
        'DAY': 'int16',
        'PRODUCT_ID': 'int32',
        'QUANTITY': 'int16',
        'SALES_VALUE': 'float32',
        'RETAIL_DISC': 'float32',
        'COUPON_DISC': 'float32',
        'COUPON_MATCH_DISC': 'float32',
        'STORE_ID': 'int16',
        'WEEK_NO': 'int8',
        'TRANS_TIME': 'int16'
    }
    
    df = pd.read_csv(RAW_DIR / "transaction_data.csv", dtype=dtype_spec)
    print(f"  Loaded {len(df):,} rows")
    return df

def clean_transactions(df):
    """Apply all cleaning transformations."""
    initial_count = len(df)
    
    # Step 1: Remove positive discounts (surcharges)
    print("\nStep 1: Removing positive discounts...")
    df = df[(df['RETAIL_DISC'] <= 0) & (df['COUPON_DISC'] <= 0)].copy()
    removed = initial_count - len(df)
    print(f"  Removed {removed} rows with positive discounts")
    
    # Step 2: Convert relative days to dates
    print("\nStep 2: Converting days to dates...")
    anchor = pd.Timestamp(ANCHOR_DATE)
    df['DATE'] = anchor + pd.to_timedelta(df['DAY'] - 1, unit='D')
    print(f"  Date range: {df['DATE'].min()} to {df['DATE'].max()}")
    
    # Step 3: Parse transaction time
    print("\nStep 3: Parsing transaction times...")
    df['TRANS_TIME_STR'] = df['TRANS_TIME'].astype(str).str.zfill(4)
    df['TIME'] = pd.to_datetime(df['TRANS_TIME_STR'], format='%H%M').dt.time
    df.drop('TRANS_TIME_STR', axis=1, inplace=True)
    
    # Step 4: Calculate total discount (absolute value)
    print("\nStep 4: Calculating total discount...")
    df['TOTAL_DISCOUNT_ABS'] = (df['RETAIL_DISC'] + df['COUPON_DISC']).abs()
    
    return df

def save_output(df):
    """Save cleaned data to processed folder."""
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    
    output_path = PROCESSED_DIR / "fact_transactions.csv"
    df.to_csv(output_path, index=False)
    print(f"\n✅ Saved to {output_path}")
    print(f"   Final row count: {len(df):,}")

def main():
    print("=" * 50)
    print("TRANSACTION DATA CLEANING PIPELINE")
    print("=" * 50)
    
    df = load_transactions()
    df = clean_transactions(df)
    save_output(df)
    
    print("\n" + "=" * 50)
    print("PIPELINE COMPLETE")
    print("=" * 50)

if __name__ == "__main__":
    main()