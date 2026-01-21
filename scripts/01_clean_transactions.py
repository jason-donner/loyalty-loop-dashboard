"""
01_clean_transactions.py
Production Data Cleaning Pipeline.

CORE LOGIC:
1. Semantic Filter: Removes known non-grocery categories (Fuel).
2. Economic Filter: Removes non-merchandise rows (Points/Tokens) based on Unit Price < $0.05.
   - This surgically separates valid 'Misc' merchandise from administrative points.
3. Safety Cap: Removes remaining anomalies with Quantity > 150.
"""

import pandas as pd
import numpy as np
from pathlib import Path

# --- CONFIGURATION ---
RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")
ANCHOR_DATE = "2024-01-01"
QTY_CAP = 150
MIN_UNIT_PRICE = 0.05

def load_data():
    """Loads raw transaction and product data with strict type enforcement."""
    print("Loading data...")
    # Enforce int64 for IDs to ensure successful merging
    trans = pd.read_csv(RAW_DIR / "transaction_data.csv", dtype={'PRODUCT_ID': 'int64', 'household_key': 'int64'})
    prod = pd.read_csv(RAW_DIR / "product.csv", dtype={'PRODUCT_ID': 'int64'})
    return trans, prod

def clean_transactions(trans, prod):
    """Executes the cleaning pipeline."""
    print(f"Initial Rows: {len(trans):,}")
    initial_rev = trans['SALES_VALUE'].sum()
    
    # 1. ENRICHMENT
    # Merge Product Category for semantic filtering
    trans = trans.merge(prod[['PRODUCT_ID', 'COMMODITY_DESC']], on='PRODUCT_ID', how='left')
    trans['COMMODITY_DESC'] = trans['COMMODITY_DESC'].fillna('UNKNOWN')

    # 2. SURGICAL FILTERING
    print("\nStep 2: Applying Surgical Filters...")
    
    # A. Semantic Filter (Fuel)
    # Catches Fuel/Gasoline explicitly as it may exceed the economic price floor
    fuel_mask = trans['COMMODITY_DESC'].str.contains('FUEL|GASOLINE', case=False, na=False)
    
    # B. Economic Filter (Row-Level)
    # Identifies administrative items (Points/Tokens) via implied unit price.
    # Logic: If Price < $0.05 AND Sales > 0, it is not physical merchandise.
    unit_price = trans['SALES_VALUE'] / trans['QUANTITY']
    non_merch_mask = (unit_price < MIN_UNIT_PRICE) & (trans['SALES_VALUE'] > 0)
    
    # Execute Removal
    remove_mask = fuel_mask | non_merch_mask
    grocery_df = trans[~remove_mask].copy()
    
    print(f"  > Removed {remove_mask.sum():,} rows identified as Non-Merchandise (Fuel/Points).")

    # 3. SAFETY CAP
    print("\nStep 3: Applying Quantity Safety Cap...")
    # Removes data entry errors (e.g., fat-finger scans) for remaining valid items
    outlier_mask = grocery_df['QUANTITY'] > QTY_CAP
    
    if outlier_mask.sum() > 0:
        print(f"  > Removed {outlier_mask.sum():,} outliers exceeding {QTY_CAP} units.")
        grocery_df = grocery_df[~outlier_mask].copy()
        
    # 4. STANDARDIZATION
    print("\nStep 4: Standardizing Dates & Metrics...")
    
    # Remove negative discounts (accounting artifacts)
    grocery_df = grocery_df[grocery_df['RETAIL_DISC'] <= 0]
    
    # Calculate Date from Day Index
    anchor = pd.Timestamp(ANCHOR_DATE)
    grocery_df['DATE'] = anchor + pd.to_timedelta(grocery_df['DAY'] - 1, unit='D')
    
    # Create absolute discount field for downstream analysis
    grocery_df['TOTAL_DISCOUNT_ABS'] = (grocery_df['RETAIL_DISC'] + grocery_df['COUPON_DISC']).abs()
    
    # Drop helper columns
    grocery_df.drop(columns=['COMMODITY_DESC'], inplace=True)
    
    # 5. REPORTING
    final_rev = grocery_df['SALES_VALUE'].sum()
    print(f"\n=== FINAL CLEANING REPORT ===")
    print(f"Grocery Rows:     {len(grocery_df):,}")
    print(f"Revenue Retained: {(final_rev/initial_rev)*100:.2f}%")
    
    return grocery_df

def main():
    trans, prod = load_data()
    clean_df = clean_transactions(trans, prod)
    
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    clean_df.to_csv(PROCESSED_DIR / "fact_transactions.csv", index=False)
    print("\n✅ Cleaned data saved to 'data/processed/fact_transactions.csv'")

if __name__ == "__main__":
    main()