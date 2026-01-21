"""
02_build_dimensions.py
Creates dimension tables for the star schema.

Author: Jason Donner
Date: 15-01-2026
"""

import pandas as pd
from pathlib import Path

RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")
ANCHOR_DATE = "2024-01-01"

def build_dim_household():
    """Build household dimension with all 2,500 households."""
    print("\nBuilding dim_household...")
    
    # Load demographics
    demog = pd.read_csv(RAW_DIR / "hh_demographic.csv")
    
    # Load all household keys from transactions
    trans = pd.read_csv(RAW_DIR / "transaction_data.csv", usecols=['household_key'])
    all_households = pd.DataFrame({'household_key': trans['household_key'].unique()})
    
    # Left join to preserve all households
    dim = all_households.merge(demog, on='household_key', how='left')
    
    # Fill missing demographics
    fill_cols = ['AGE_DESC', 'MARITAL_STATUS_CODE', 'INCOME_DESC', 
                 'HOMEOWNER_DESC', 'HH_COMP_DESC', 'HOUSEHOLD_SIZE_DESC', 
                 'KID_CATEGORY_DESC']
    dim[fill_cols] = dim[fill_cols].fillna('Unknown')
    
    print(f"  Total households: {len(dim):,}")
    print(f"  With demographics: {(dim['AGE_DESC'] != 'Unknown').sum():,}")
    
    dim.to_csv(PROCESSED_DIR / "dim_household.csv", index=False)
    return dim

def build_dim_product():
    """Build product dimension."""
    print("\nBuilding dim_product...")
    
    dim = pd.read_csv(RAW_DIR / "product.csv")
    dim.to_csv(PROCESSED_DIR / "dim_product.csv", index=False)
    
    print(f"  Total products: {len(dim):,}")
    return dim

def build_dim_campaign():
    """Build campaign dimension with derived fields."""
    print("\nBuilding dim_campaign...")
    
    dim = pd.read_csv(RAW_DIR / "campaign_desc.csv")
    
    # Add friendly type labels
    type_map = {
        'TypeA': 'Personalized',
        'TypeB': 'Targeted',
        'TypeC': 'Mass'
    }
    dim['CAMPAIGN_TYPE_LABEL'] = dim['DESCRIPTION'].map(type_map)
    
    # Convert days to dates
    anchor = pd.Timestamp(ANCHOR_DATE)
    dim['START_DATE'] = anchor + pd.to_timedelta(dim['START_DAY'] - 1, unit='D')
    dim['END_DATE'] = anchor + pd.to_timedelta(dim['END_DAY'] - 1, unit='D')
    
    # Calculate duration
    dim['DURATION_DAYS'] = dim['END_DAY'] - dim['START_DAY']
    
    dim.to_csv(PROCESSED_DIR / "dim_campaign.csv", index=False)
    
    print(f"  Total campaigns: {len(dim):,}")
    return dim

def build_dim_calendar():
    """Build calendar dimension for date intelligence."""
    print("\nBuilding dim_calendar...")
    
    # Get date range from transactions
    trans = pd.read_csv(RAW_DIR / "transaction_data.csv", usecols=['DAY'])
    min_day, max_day = trans['DAY'].min(), trans['DAY'].max()
    
    anchor = pd.Timestamp(ANCHOR_DATE)
    dates = pd.date_range(
        start=anchor + pd.Timedelta(days=min_day-1),
        end=anchor + pd.Timedelta(days=max_day-1),
        freq='D'
    )
    
    dim = pd.DataFrame({'Date': dates})
    dim['DAY'] = range(min_day, max_day + 1)
    dim['Day_of_Week'] = dim['Date'].dt.dayofweek + 1  # 1=Monday
    dim['Day_Name'] = dim['Date'].dt.day_name()
    dim['Day_of_Month'] = dim['Date'].dt.day
    dim['Week_of_Year'] = dim['Date'].dt.isocalendar().week
    dim['Month'] = dim['Date'].dt.month
    dim['Month_Name'] = dim['Date'].dt.month_name()
    dim['Month_Short'] = dim['Date'].dt.strftime('%b')
    dim['Quarter'] = dim['Date'].dt.quarter
    dim['Quarter_Name'] = 'Q' + dim['Quarter'].astype(str)
    dim['Year'] = dim['Date'].dt.year
    dim['Year_Month'] = dim['Date'].dt.strftime('%Y-%m')
    dim['Is_Weekend'] = dim['Day_of_Week'].isin([6, 7])
    
    dim.to_csv(PROCESSED_DIR / "dim_calendar.csv", index=False)
    
    print(f"  Date range: {dim['Date'].min()} to {dim['Date'].max()}")
    print(f"  Total days: {len(dim):,}")
    return dim

def build_fact_redemptions():
    """Build redemption fact table."""
    print("\nBuilding fact_redemptions...")
    
    df = pd.read_csv(RAW_DIR / "coupon_redempt.csv")
    
    # Add date
    anchor = pd.Timestamp(ANCHOR_DATE)
    df['DATE'] = anchor + pd.to_timedelta(df['DAY'] - 1, unit='D')
    
    df.to_csv(PROCESSED_DIR / "fact_redemptions.csv", index=False)
    
    print(f"  Total redemptions: {len(df):,}")
    return df

def main():
    print("=" * 50)
    print("BUILDING DIMENSION TABLES")
    print("=" * 50)
    
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    
    build_dim_household()
    build_dim_product()
    build_dim_campaign()
    build_dim_calendar()
    build_fact_redemptions()
    
    print("\n" + "=" * 50)
    print("ALL DIMENSIONS BUILT")
    print("=" * 50)

if __name__ == "__main__":
    main()