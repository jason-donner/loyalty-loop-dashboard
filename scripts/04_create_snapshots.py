"""
04_create_snapshots.py
Creates a periodic snapshot fact table ('fact_monthly_snapshots').

PURPOSE:
This table tracks the state of every customer at the end of every month.
It allows for "time travel" analysis (e.g., "How many At-Risk customers did we have in Jan vs Feb?").

EXPERT FEATURES:
1. Zero-Fill Spine: Tracks customers even in months they don't buy (crucial for churn).
2. Lapsed Days Calculation: Precise 'Days Since Last Purchase' for every month-end.
3. Rolling Metrics: 3-Month Rolling Spend to detect value degradation before churn.
4. Strategic Status: Auto-assigns 'Active', 'At-Risk', 'Churned' based on the 30-day rule.
"""

import pandas as pd
import numpy as np
from pathlib import Path

# --- CONFIGURATION ---
PROCESSED_DIR = Path("data/processed")
OUTPUT_FILE = PROCESSED_DIR / "fact_monthly_snapshots.csv"

def load_transactions():
    """Load cleaned transaction data."""
    print("Loading transactions...")
    df = pd.read_csv(PROCESSED_DIR / "fact_transactions.csv", parse_dates=['DATE'])
    return df

def create_customer_month_spine(df):
    """
    Creates a 'Cross Join' of All Customers x All Months.
    Ensures we have a record for every customer every month, even if they bought nothing.
    """
    print("Generating Customer-Month Spine...")
    
    # 1. Get Date Range (Month Start)
    min_date = df['DATE'].min().replace(day=1)
    max_date = df['DATE'].max().replace(day=1)
    all_months = pd.date_range(start=min_date, end=max_date, freq='MS') # MS = Month Start
    
    # 2. Get Unique Households
    unique_households = df['household_key'].unique()
    
    # 3. Create Cross Product (The Spine)
    # Using MultiIndex for efficient creation
    index = pd.MultiIndex.from_product(
        [unique_households, all_months], 
        names=['household_key', 'Month_Start']
    )
    
    spine_df = pd.DataFrame(index=index).reset_index()
    print(f"  > Created spine with {len(spine_df):,} rows ({len(unique_households)} HHs x {len(all_months)} Months)")
    
    return spine_df

def calculate_monthly_metrics(df, spine_df):
    """Aggregates transactions to the monthly level and merges with spine."""
    print("Calculating Monthly Metrics...")
    
    # 1. Aggregate Transactions by Month
    df['Month_Start'] = df['DATE'].dt.to_period('M').dt.to_timestamp() # Normalizing to Month Start
    
    monthly_aggs = df.groupby(['household_key', 'Month_Start']).agg({
        'SALES_VALUE': 'sum',
        'BASKET_ID': 'nunique',
        'DATE': 'max' # Last purchase date in that specific month
    }).reset_index().rename(columns={
        'SALES_VALUE': 'Monthly_Spend',
        'BASKET_ID': 'Monthly_Visits',
        'DATE': 'Last_Purchase_This_Month'
    })
    
    # 2. Merge with Spine (Left Join to keep zero-purchase months)
    snapshot = spine_df.merge(monthly_aggs, on=['household_key', 'Month_Start'], how='left')
    
    # 3. Fill NaNs for Activity Metrics
    snapshot['Monthly_Spend'] = snapshot['Monthly_Spend'].fillna(0)
    snapshot['Monthly_Visits'] = snapshot['Monthly_Visits'].fillna(0)
    
    return snapshot

def calculate_history_and_status(snapshot):
    """
    The 'Time Machine' logic:
    - Forward fills purchase dates to calculate Lapsed Days.
    - Calculates Rolling Spend.
    - Assigns Status based on the 30-day rule.
    """
    print("Calculating History & Status...")
    
    # Sort is critical for forward fill and rolling windows
    snapshot = snapshot.sort_values(['household_key', 'Month_Start'])
    
    # 1. Calculate 'Last_Purchase_Anytime' (Forward Fill)
    # If a user didn't buy this month, their last purchase was in a previous month.
    snapshot['Last_Purchase_Anytime'] = snapshot.groupby('household_key')['Last_Purchase_This_Month'].ffill()
    
    # 2. Calculate Lapsed Days (Metric for Churn)
    # Reference Point: End of the Snapshot Month
    snapshot['Month_End'] = snapshot['Month_Start'] + pd.offsets.MonthEnd(0)
    
    # Days between Month End and Last Purchase
    snapshot['Lapsed_Days'] = (snapshot['Month_End'] - snapshot['Last_Purchase_Anytime']).dt.days
    
    # Handle New Customers (NaN Lapsed Days means they haven't started yet)
    snapshot['Lapsed_Days'] = snapshot['Lapsed_Days'].fillna(999).astype(int)
    
    # 3. Rolling 3-Month Spend (Trend Indicator)
    # Helps identify "High Value" churners
    snapshot['Rolling_3M_Spend'] = snapshot.groupby('household_key')['Monthly_Spend']\
                                           .rolling(window=3, min_periods=1).sum().reset_index(0, drop=True)
    
    # 4. Assign Strategic Status (Based on METHODOLOGY.md)
    # Active: <= 14 Days
    # At-Risk: 15 - 30 Days (Intervention Window)
    # Churned: > 30 Days
    
    conditions = [
        (snapshot['Lapsed_Days'] <= 14),
        (snapshot['Lapsed_Days'] <= 30),
        (snapshot['Lapsed_Days'] < 999) # Churned (but not future/unknown)
    ]
    choices = ['Active', 'At-Risk', 'Churned']
    
    snapshot['Status'] = np.select(conditions, choices, default='New/Unknown')
    
    return snapshot

def create_current_state(df):
    """
    Generates a current-state dimension based on the global latest date in the dataset.
    This provides the operational 'Who to call today' list.
    """
    print("Generating Current Customer State Dimension...")
    
    # 1. Define 'Today' as the absolute maximum date in the entire transaction log
    global_max_date = df['DATE'].max()
    
    # 2. Get the absolute last purchase date for every household
    current_state = df.groupby('household_key')['DATE'].max().reset_index()
    current_state = current_state.rename(columns={'DATE': 'Last_Purchase_Date'})
    
    # 3. Calculate True Lapsed Days
    current_state['Current_Lapsed_Days'] = (global_max_date - current_state['Last_Purchase_Date']).dt.days
    
    # 4. Assign Strategic Status
    conditions = [
        (current_state['Current_Lapsed_Days'] <= 14),
        (current_state['Current_Lapsed_Days'] <= 30),
        (current_state['Current_Lapsed_Days'] < 999)
    ]
    choices = ['Active', 'At-Risk', 'Churned']
    
    current_state['Current_Status'] = np.select(conditions, choices, default='Unknown')
    
    return current_state

def main():
    print("="*50)
    print("SNAPSHOT & CURRENT STATE GENERATOR")
    print("="*50)
    
    # 1. Load
    df = load_transactions()
    
    # --- NEW: Generate Current State Dimension ---
    dim_current_state = create_current_state(df)
    current_output_file = PROCESSED_DIR / "dim_customer_current.csv"
    print(f"\nSaving Current State to {current_output_file}...")
    dim_current_state.to_csv(current_output_file, index=False)
    
    # --- EXISTING: Generate Historical Snapshots ---
    spine = create_customer_month_spine(df)
    snapshot = calculate_monthly_metrics(df, spine)
    final_snapshot = calculate_history_and_status(snapshot)
    
    export_cols = [
        'household_key', 'Month_Start', 'Month_End', 
        'Monthly_Spend', 'Monthly_Visits', 'Rolling_3M_Spend',
        'Lapsed_Days', 'Status'
    ]
    final_snapshot = final_snapshot[export_cols]
    
    print(f"\nSaving Snapshots to {OUTPUT_FILE}...")
    final_snapshot.to_csv(OUTPUT_FILE, index=False)
    print("Generation complete.")

if __name__ == "__main__":
    main()