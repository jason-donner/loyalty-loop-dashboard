"""
03_calculate_rfm.py
Calculates RFM scores for all households.

Author: Jason Donner
Date: 16-01-2026
"""

import pandas as pd
import numpy as np
from pathlib import Path

PROCESSED_DIR = Path("data/processed")

def calculate_rfm():
    """Calculate Recency, Frequency, Monetary for each household."""
    print("Loading transaction data...")
    df = pd.read_csv(PROCESSED_DIR / "fact_transactions.csv", parse_dates=['DATE'])
    
    # Analysis date = last date in dataset
    analysis_date = df['DATE'].max()
    print(f"Analysis date: {analysis_date}")
    
    # Aggregate by household
    print("\nCalculating RFM metrics...")
    rfm = df.groupby('household_key').agg({
        'DATE': lambda x: (analysis_date - x.max()).days,  # Recency
        'BASKET_ID': 'nunique',  # Frequency
        'SALES_VALUE': 'sum'  # Monetary
    }).reset_index()
    
    rfm.columns = ['household_key', 'Recency_Days', 'Frequency', 'Monetary']
    
    print(f"  Households: {len(rfm)}")
    print(f"  Recency range: {rfm['Recency_Days'].min()} - {rfm['Recency_Days'].max()} days")
    print(f"  Frequency range: {rfm['Frequency'].min()} - {rfm['Frequency'].max()} trips")
    print(f"  Monetary range: ${rfm['Monetary'].min():.2f} - ${rfm['Monetary'].max():.2f}")
    
    return rfm

def assign_scores(rfm):
    """Assign quintile scores (1-5)."""
    print("\nAssigning quintile scores...")
    
    # Recency: Lower is better (more recent)
    rfm['R_Score'] = pd.qcut(rfm['Recency_Days'], 5, labels=[5, 4, 3, 2, 1])
    
    # Frequency: Higher is better
    rfm['F_Score'] = pd.qcut(rfm['Frequency'].rank(method='first'), 5, labels=[1, 2, 3, 4, 5])
    
    # Monetary: Higher is better
    rfm['M_Score'] = pd.qcut(rfm['Monetary'].rank(method='first'), 5, labels=[1, 2, 3, 4, 5])
    
    # Convert to int
    rfm['R_Score'] = rfm['R_Score'].astype(int)
    rfm['F_Score'] = rfm['F_Score'].astype(int)
    rfm['M_Score'] = rfm['M_Score'].astype(int)
    
    # Combined score
    rfm['RFM_Score'] = (rfm['R_Score'].astype(str) + 
                        rfm['F_Score'].astype(str) + 
                        rfm['M_Score'].astype(str))
    
    return rfm

def assign_segments(rfm):
    """Assign customer segments based on RFM scores."""
    print("\nAssigning segments...")
    
    def get_segment(row):
        r, f, m = row['R_Score'], row['F_Score'], row['M_Score']
        
        if r >= 4 and f >= 4 and m >= 4:
            return 'Champions'
        elif r >= 3 and f >= 4:
            return 'Loyal'
        elif r >= 4 and f == 3 and m >= 3:
            return 'Potential Loyal'
        elif r == 5 and f <= 2:
            return 'New'
        elif r >= 4 and f <= 2 and m >= 3:
            return 'Promising'
        elif r == 3 and f == 3:
            return 'Needs Attention'
        elif r <= 3 and r >= 2 and f <= 2:
            return 'About to Sleep'
        elif r == 2 and f >= 3:
            return 'At Risk'
        elif r == 1 and f >= 2:
            return 'Hibernating'
        else:
            return 'Lost'
    
    rfm['RFM_Segment'] = rfm.apply(get_segment, axis=1)
    
    # Lifecycle stage
    def get_lifecycle(row):
        r = row['Recency_Days']
        f = row['Frequency']
        if r <= 30 and f < 3:
            return 'New'
        elif r <= 60:
            return 'Active'
        elif r <= 90:
            return 'At-Risk'
        else:
            return 'Churned'
    
    rfm['Lifecycle_Stage'] = rfm.apply(get_lifecycle, axis=1)
    
    return rfm

def main():
    print("=" * 50)
    print("RFM CALCULATION")
    print("=" * 50)
    
    rfm = calculate_rfm()
    rfm = assign_scores(rfm)
    rfm = assign_segments(rfm)
    
    # Summary
    print("\n=== SEGMENT DISTRIBUTION ===")
    print(rfm['RFM_Segment'].value_counts())
    
    print("\n=== LIFECYCLE DISTRIBUTION ===")
    print(rfm['Lifecycle_Stage'].value_counts())
    
    # Save
    output_path = PROCESSED_DIR / "dim_rfm.csv"
    rfm.to_csv(output_path, index=False)
    print(f"\n✅ Saved to {output_path}")

if __name__ == "__main__":
    main()