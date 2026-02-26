# Methodology

## Loyalty Loop: Customer Lifecycle & Campaign ROI Analytics

> Detailed documentation of data architecture decisions, statistical justifications, and business logic.

***

## Table of Contents

1. [Churn Definition & Inter Purchase Intervals](#1-churn-definition--inter-purchase-intervals)
2. [Strategic RFM Segmentation](#2-strategic-rfm-segmentation)
3. [Control Group Campaign Attribution](#3-control-group-campaign-attribution)
4. [Promotional Lift & Synergy Analysis](#4-promotional-lift--synergy-analysis)
5. [Architectural Evolution: Resolving Cartesian Explosions](#5-architectural-evolution-resolving-cartesian-explosions)
6. [Data Quality & Engine Optimization](#6-data-quality--engine-optimization)
7. [Limitations & Assumptions](#7-limitations--assumptions)

***

## 1. Churn Definition & Inter Purchase Intervals

### The Analytical Problem

Defining "churn" requires balancing statistical signals with operational feasibility. The industry standard default often suggests 90 days. However, high frequency grocery shoppers establish habits much faster. Waiting 90 days to flag a missing customer in a high velocity environment means the customer is already lost.

My objective was to audit the standard 90 day assumption and derive a threshold specific to the actual shopping cadence of this customer base.

### Step 1: Calculate Inter Purchase Intervals

I analyzed the gap between shopping trips (baskets) rather than individual line items to capture true visit frequency.

```python
# Calculate days between VISITS (unique Basket IDs)
baskets = df[['household_key', 'DATE']].drop_duplicates().sort_values(['household_key', 'DATE'])
baskets['prev_date'] = baskets.groupby('household_key')['DATE'].shift(1)
baskets['days_between'] = (baskets['DATE'] - baskets['prev_date']).dt.days
```

### Step 2: Distribution Analysis

| Statistic | Value | Interpretation |
| :--- | :--- | :--- |
| **Count** | 223,033 intervals | Suitable sample size. |
| **Mean** | 7.3 days | Average interval is approximately 1 week. |
| **Median** | 4.0 days | Typical behavior is twice weekly visits. |
| **90th Percentile** | 14.0 days | 90% of return trips happen within 14 days. |
| **Upper Fence** | 14.5 days | Statistical outlier threshold. |

**Interpretation:** The median customer returns every 4 days. A 90 day threshold (22 times the median) is a reactive autopsy, not a proactive indicator.

### Step 3: Threshold Selection

I shifted the operational definition from Quarterly (90 days) to Monthly (30 days). A 30 day threshold aligns with the statistical upper fence for outliers while providing a buffer for standard routine breaks (e.g., vacations).

| Stage | Definition | Business Logic |
| :--- | :--- | :--- |
| **Active** | Last purchase <= 14 days | Normal weekly or bi weekly routine. |
| **At Risk** | Last purchase 15 to 30 days | **Immediate Intervention.** Customer has missed 2 to 4 expected cycles. |
| **Churned** | Last purchase > 30 days | Habit is broken. |

***

## 2. Strategic RFM Segmentation

### The Analytical Fix

Standard RFM quintiles fail in high velocity retail because they ignore the operational 30 day churn threshold, often grouping customers who have not shopped in 90 days as simply "At Risk." I implemented a **Strategic RFM** model, hard coding the Recency bins to match my verified shopping cycle.

### Recency (R) Logic

| Score | Status | Days Since Purchase | Action Strategy |
| :--- | :--- | :--- | :--- |
| **5** | Active (Habitual) | 0 to 7 days | Reward and Maintain. |
| **4** | Active (Slipping) | 8 to 14 days | Upsell basket builders. |
| **3** | **At Risk (Warning)** | **15 to 30 days** | **Intervene (The 15 to 30 day Kill Zone).** |
| **2** | Churned (Recent) | 31 to 60 days | Win back campaigns. |
| **1** | Lost (Long term) | 61+ days | Suppress from marketing spend. |

*Note: Frequency (F) and Monetary (M) scores were calculated as percentiles relative to Active users only (Recency >= 3) to prevent "Lost" customers from skewing the grading curve.*

***

## 3. Control Group Campaign Attribution

### The Challenge

Measuring marketing ROI is prone to selection bias. Customers who redeem coupons are inherently more engaged. Comparing their spend directly to a baseline inflates the perceived value of the campaign.

### My Approach: Difference in Differences (DiD)

I deployed a Pre/Post comparison utilizing a non redeeming control group to isolate net incremental Gross Sales.

**Treatment Group:** Households who redeemed coupons during the campaign.
**Control Group:** Households enrolled in the campaign target group who did NOT redeem.
**Measurement Window:** 30 days prior to campaign start versus 30 days post campaign end.

### Results and Cannibalization Findings

| Campaign Type | Redeemer Lift | Control Lift | Net Incremental | Operational Insight |
| :--- | :--- | :--- | :--- | :--- |
| **Type C (Mass)** | +18% | +4% | **+14%** | Optimal. Highest positive behavioral change. |
| **Type B (Targeted)** | +12% | +6% | **+6%** | Moderate impact. |
| **Type A (Personalized)**| +3% | +5% | **Negative** | **Failed execution.** Cannibalized Gross Sales. |

**Strategic Conclusion:** The data disproves the assumption that personalization inherently drives growth. Type A campaigns required high operational complexity (measured via Promoted SKUs) but resulted in a negative net lift. Mass marketing provided the most efficient financial return for the store labor required.

***

## 4. Promotional Lift & Synergy Analysis

I calculated Gross Sales Lift as the percentage increase in average units sold compared to a non promoted baseline (no display, no mailer).

| Display Location \ Mailer Placement | None | Interior Page | Front Page |
| :--- | :--- | :--- | :--- |
| **Standard Shelf (None)** | 0% (Baseline) | +60% Lift | +112% Lift |
| **Rear Aisle** | +38% Lift | +124% Lift | +181% Lift |
| **Front Endcap** | **+133% Lift** | **+271% Lift** | **+371% Lift** |

**Insight:** The combination of Front Endcap and Front Page (+371%) exceeds the additive sum of the individual tactics (+133% + 112% = 245%). Integrated campaigns drive exponential value, while "Rear Aisle" displays generate diminishing returns on labor.

***

## 5. Architectural Evolution: Resolving Cartesian Explosions

### Version 1.0: The Snapshot Failure

The initial data architecture attempted to track historical customer churn using a Periodic Snapshot Fact Table (`fact_monthly_snapshots`). This generated a dense matrix of every household for every month.

When loaded into the Power BI presentation layer, this design failed at scale. Attempting to cross filter the snapshot fact table against the primary `fact_transactions` table resulted in severe many to many filter context collisions. This caused Cartesian product data explosions, duplicating rows and breaking the VertiPaq engine's rendering capacity.

### Version 2.0: The Dimensional Pivot

To resolve this, I refactored the Python ETL pipeline to abandon the snapshot logic and output a strict `dim_customer_current` dimension table.

1. **Grain Control:** The script was rewritten to isolate the absolute `MAX(transaction_date)` per `household_key`.
2. **Static Attributes:** Current status and lapsed days were calculated as static attributes tied to that single date.
3. **Star Schema Enforcement:** This enforced a strict one to many relationship between the customer dimension and the transaction fact table.

This pivot eliminated the Cartesian explosions, allowing for precise row level evaluation contexts and sub second micro level drill throughs in the UI.

***

## 6. Data Quality & Engine Optimization

### The "Fuel" and Points Contamination

A semantic and economic filter was applied in Python to purge approximately 25,000 non merchandise rows.

1. **Fuel:** Removed via keyword filter ("FUEL", "GASOLINE").
2. **Points:** Removed via economic filter (Unit Price < $0.05).
This prevented high quantity/low value accounting entries from destroying core operational metrics.

### VertiPaq Engine Optimization

The Power BI model was audited using the external XMLA endpoint tool, Measure Killer.

* Unused source columns (e.g., redundant transaction IDs) were physically removed in Power Query to reduce columnar memory bloat.
* Orphaned DAX measures resulting from the Version 1.0 snapshot architecture were permanently deleted to maintain a lean, enterprise grade data dictionary.

***

## 7. Limitations & Assumptions

1. **Attribution Window:** I assumed a 30 day Pre/Post window is robust for campaign measurement as it captures approximately 7 to 10 average shopping cycles. Long term "halo effects" beyond 30 days are excluded.
2. **No Cost Data:** The dataset lacks Campaign Cost and Product Cost metrics. I assumed Gross Sales Lift and Redemption Rate are sufficient proxies for operational efficiency, but I cannot calculate true net profit margin.
3. **Operational Complexity Proxy:** I assumed the count of unique `COUPON_UPC`s (Promoted SKUs) accurately serves as a proxy for the physical store labor required to execute a campaign.
