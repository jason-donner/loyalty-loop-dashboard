"""
03_calculate_rfm.py
Calculates Strategic RFM scores aligned to the 30-Day Churn Threshold.

LOGIC CHANGES (v2):
1. Recency: Hard-coded business cycles (Weekly, Bi-Weekly, Monthly).
   - NOT statistical quintiles.
2. F/M Scores: Calculated relative to ACTIVE users only (R_Score >= 3).
   - Prevents long-term churners from skewing the curve for active shoppers.
3. Segments: Aligned to the 'Intervention Window' (Days 15-30).
"""

import pandas as pd
import numpy as np
from pathlib import Path

PROCESSED_DIR = Path("data/processed")

def calculate_rfm():
    """Calculate raw Recency, Frequency, Monetary metrics."""
    print("Loading transaction data...")
    df = pd.read_csv(PROCESSED_DIR / "fact_transactions.csv", parse_dates=['DATE'])
    
    # Analysis date = last date in dataset (snapshot)
    analysis_date = df['DATE'].max()
    print(f"Analysis Date: {analysis_date.date()}")
    
    print("\nCalculating metrics...")
    rfm = df.groupby('household_key').agg({
        'DATE': lambda x: (analysis_date - x.max()).days,  # Recency
        'BASKET_ID': 'nunique',                            # Frequency
        'SALES_VALUE': 'sum'                               # Monetary
    }).reset_index()
    
    rfm.columns = ['household_key', 'Recency_Days', 'Frequency', 'Monetary']
    return rfm

def assign_strategic_scores(rfm):
    """
    Assign scores based on biological shopping cycles.
    """
    print("\nAssigning Strategic Scores...")
    
    # 1. RECENCY (Hard-coded to business logic)
    # 5: Active Habit (0-7 days) - Weekly Shopper
    # 4: Slipping (8-14 days) - Missed one cycle
    # 3: RISK ZONE (15-30 days) - The Intervention Window
    # 2: Churned (31-60 days) - Recent loss
    # 1: Lost (61+ days) - Long term
    
    def get_r_score(days):
        if days <= 7: return 5
        if days <= 14: return 4
        if days <= 30: return 3
        if days <= 60: return 2
        return 1

    rfm['R_Score'] = rfm['Recency_Days'].apply(get_r_score)
    
    # 2. FREQUENCY & MONETARY (Relative to Active Users)
    # We only score F/M for users who are nominally active (R >= 3).
    # Inactive users (R < 3) get a score of 1.
    
    active_mask = rfm['R_Score'] >= 3
    active_data = rfm[active_mask]
    
    print(f"  > Scoring F/M on {len(active_data):,} Active/At-Risk households (out of {len(rfm):,})")
    
    # Calculate Quartiles (1-4) for Active population
    # Note: We use quartiles (4 bins) to force a stricter curve than quintiles
    try:
        rfm.loc[active_mask, 'F_Score'] = pd.qcut(active_data['Frequency'].rank(method='first'), 4, labels=[1, 2, 3, 4]).astype(int)
        rfm.loc[active_mask, 'M_Score'] = pd.qcut(active_data['Monetary'].rank(method='first'), 4, labels=[1, 2, 3, 4]).astype(int)
    except ValueError as e:
        print(f"  ! Warning: Not enough unique values for qcut. Defaulting to rank. {e}")
        rfm.loc[active_mask, 'F_Score'] = 1
        rfm.loc[active_mask, 'M_Score'] = 1

    # Fill Churned/Lost users with 1s
    rfm[['F_Score', 'M_Score']] = rfm[['F_Score', 'M_Score']].fillna(1).astype(int)
    
    # Combined String Score for readability (e.g., "544")
    rfm['RFM_Score'] = (rfm['R_Score'].astype(str) + 
                        rfm['F_Score'].astype(str) + 
                        rfm['M_Score'].astype(str))
    
    return rfm

def assign_segments(rfm):
    """Map scores to Business Segments."""
    print("\nMapping Segments...")
    
    def get_segment(row):
        r, f = row['R_Score'], row['F_Score']
        
        if r == 5 and f == 4: return 'Champions'
        if r >= 4 and f >= 3: return 'Loyalists'
        if r >= 4 and f <= 2: return 'Potential Loyal'
        if r == 3:            return 'At Risk (Intervention)' # 15-30 Days
        if r == 2:            return 'Hibernating'            # 31-60 Days
        return 'Lost'                                         # 60+ Days
    
    rfm['RFM_Segment'] = rfm.apply(get_segment, axis=1)
    
    # High-level Lifecycle Stage
    def get_lifecycle(r_score):
        if r_score >= 4: return 'Active'
        if r_score == 3: return 'At-Risk'
        return 'Churned'
        
    rfm['Lifecycle_Stage'] = rfm['R_Score'].apply(get_lifecycle)
    
    return rfm

def main():
    print("="*50)
    print("STRATEGIC RFM PIPELINE (30-Day Threshold)")
    print("="*50)
    
    rfm = calculate_rfm()
    rfm = assign_strategic_scores(rfm)
    rfm = assign_segments(rfm)
    
    # Summary Report
    print("\n=== SEGMENT DISTRIBUTION ===")
    summary = rfm.groupby(['RFM_Segment', 'Lifecycle_Stage']).agg({
        'household_key': 'count',
        'Recency_Days': 'mean'
    }).rename(columns={'household_key': 'Count', 'Recency_Days': 'Avg_Recency'}).sort_values('Avg_Recency')
    
    print(summary)
    
    # Save
    output_path = PROCESSED_DIR / "dim_rfm.csv"
    rfm.to_csv(output_path, index=False)
    print(f"\n Saved Strategic RFM to {output_path}")

if __name__ == "__main__":
    main()