# Data Dictionary

## Loyalty Loop: Customer Lifecycle & Campaign ROI Analytics

> Complete reference for all tables and fields in the analytical data model.

---

## Table Overview

| Table | Type | Grain | Row Count | Primary Key | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `fact_transactions` | Fact | Line item per basket | ~2,570,000 | BASKET_ID + PRODUCT_ID + DAY | Cleaned purchases (No Fuel/Points). |
| `fact_redemptions` | Fact | Coupon redemption | 2,318 | household_key + COUPON_UPC + DAY | Coupon usage records. |
| `dim_household` | Dimension | Household | 2,500 | household_key | Customer demographics. |
| `dim_customer_current`| Dimension | Household | 2,500 | household_key | Current lifecycle state. |
| `dim_product` | Dimension | Product | 92,353 | PRODUCT_ID | Product hierarchy. |
| `dim_campaign` | Dimension | Campaign | 30 | CAMPAIGN | Campaign metadata. |
| `dim_calendar` | Dimension | Day | 711 | Date | Date attributes. |
| `dim_rfm` | Dimension | Household | 2,500 | household_key | Strategic RFM Scores & Segments. |

---

## fact_transactions

### fact_transactions Description

Contains all valid merchandise purchases. I surgically removed administrative items (Loyalty Points) and Non-Merchandise (Fuel) at the Python source level to ensure accurate basket metrics in the presentation layer.

### fact_transactions Source

- **Original file:** `transaction_data.csv`
- **Cleaning:** `scripts/01_clean_transactions.py` (Economic & Semantic Filters applied)

### fact_transactions Columns

| Column | Data Type | Nullable | Description |
| :--- | :--- | :--- | :--- |
| `household_key` | INT | No | Foreign key to dim_household. Unique identifier for the purchasing household. |
| `BASKET_ID` | BIGINT | No | Unique identifier for the shopping trip. |
| `DAY` | INT | No | Relative day number (1-711). |
| `DATE` | DATE | No | Absolute date calculated as: 2024-01-01 + (DAY - 1) days. |
| `PRODUCT_ID` | INT | No | Foreign key to dim_product. |
| `QUANTITY` | INT | No | Number of units purchased. **Safety Cap:** I removed rows > 150 units. |
| `SALES_VALUE` | DECIMAL(10,2) | No | Gross Sales received. **Economic Filter:** I removed rows with Unit Price < $0.05. |
| `RETAIL_DISC` | DECIMAL(10,2) | No | Loyalty card discount. Always <= 0 (I removed positive values). |
| `COUPON_DISC` | DECIMAL(10,2) | No | Manufacturer coupon discount. Always <= 0. |
| `COUPON_MATCH_DISC` | DECIMAL(10,2) | No | Retailer reimbursement. Does not affect customer price. |
| `TRANS_TIME` | TIME | No | Transaction time (HHMM parsed to Time). |
| `STORE_ID` | INT | No | Store location identifier. |
| `WEEK_NO` | INT | No | Week number (1-102). |
| `TOTAL_DISCOUNT_ABS` | DECIMAL(10,2) | No | Derived: ABS(RETAIL_DISC + COUPON_DISC). |

### fact_transactions Data Quality Rules

1. **Fuel Removal:** I removed rows containing "FUEL" or "GASOLINE" in the commodity description.
2. **Points Removal:** I removed rows with `Unit Price < $0.05` (~25k rows).
3. **Positive Discount Fix:** I removed rows with `RETAIL_DISC > 0`.

---

## dim_customer_current

### dim_customer_current Description

I engineered this dimension table to replace the legacy periodic snapshot fact table (`fact_monthly_snapshots`). By enforcing a strict one-to-one grain per household based on their maximum transaction date, I eliminated the Cartesian product explosions that previously crashed the VertiPaq engine.

### dim_customer_current Source

- **Generated:** `scripts/04_build_current_customer_state.py`
- **Grain:** One row per Household.

### dim_customer_current Columns

| Column | Data Type | Description |
| :--- | :--- | :--- |
| `household_key` | INT | Primary key. Links to `dim_household`. |
| `Max_Transaction_Date`| DATE | The absolute latest date the customer made a purchase. |
| `Current_Lapsed_Days` | INT | Days since last purchase (calculated against the maximum dataset date). |
| `Current_Status` | VARCHAR | **Strategic State:** 'Active' (0-14d), 'At-Risk' (15-30d), 'Churned' (>30d). |

---

## dim_rfm

### dim_rfm Description

Strategic RFM scores. I calculated these in Python using my custom 30-Day Churn Threshold. Unlike standard quintiles, I hard-coded Recency to shopping cycles to ensure the metric was operationally relevant.

### dim_rfm Source

- **Generated:** `scripts/03_calculate_rfm.py`
- **Logic:** Strategic Scoring (See Methodology document).

### dim_rfm Columns

| Column | Data Type | Description |
| :--- | :--- | :--- |
| `household_key` | INT | Primary key. |
| `Recency_Days` | INT | Days since last purchase (relative to max date). |
| `Frequency` | INT | Count of distinct baskets (Lifetime). |
| `Monetary` | DECIMAL | Total lifetime Gross Sales. |
| `R_Score` | INT | **Strategic Recency:** 5=Active(0-7d), 4=Slipping(8-14d), 3=Risk(15-30d), 1-2=Churned. |
| `F_Score` | INT | Frequency Quartile (1-4). **Calculated relative to Active users only.** |
| `M_Score` | INT | Monetary Quartile (1-4). **Calculated relative to Active users only.** |
| `RFM_Segment` | VARCHAR | Business-ready label (e.g., 'At Risk'). |

---

## fact_redemptions

### fact_redemptions Description

Records of coupon redemptions linked to specific marketing campaigns.

### fact_redemptions Columns

| Column | Data Type | Description |
| :--- | :--- | :--- |
| `household_key` | INT | Foreign key to dim_household. |
| `DATE` | DATE | Absolute date of redemption. |
| `COUPON_UPC` | BIGINT | Coupon identifier (Used to calculate Promoted SKUs). |
| `CAMPAIGN` | INT | Foreign key to dim_campaign. |

---

## dim_household

### dim_household Description

Demographic information. **Coverage:** ~32% of households. I filled missing values with 'Unknown' to prevent dropping valid transaction data.

### dim_household Columns

| Column | Data Type | Valid Values |
| :--- | :--- | :--- |
| `household_key` | INT | 1-2500 |
| `AGE_DESC` | VARCHAR | 19-24, 25-34, 35-44, 45-54, 55-64, 65+, Unknown |
| `INCOME_DESC` | VARCHAR | Under 15K ... 250K+, Unknown |
| `HH_COMP_DESC` | VARCHAR | Household composition (e.g., 2 Adults Kids). |
| `KID_CATEGORY_DESC`| VARCHAR | 1, 2, 3+, None/Unknown |

---

## dim_product

### dim_product Description

Product hierarchy.

### dim_product Columns

| Column | Data Type | Description |
| :--- | :--- | :--- |
| `PRODUCT_ID` | INT | Primary Key. |
| `DEPARTMENT` | VARCHAR | Top-level (GROCERY, MEAT, DRUG GM). |
| `COMMODITY_DESC` | VARCHAR | Mid-level category (e.g., SOFT DRINKS). |
| `SUB_COMMODITY_DESC`| VARCHAR | Granular category. |
| `BRAND` | VARCHAR | National or Private. |

---

## dim_campaign

### dim_campaign Description

Marketing campaign metadata.

### dim_campaign Columns

| Column | Data Type | Description |
| :--- | :--- | :--- |
| `CAMPAIGN` | INT | Primary Key (1-30). |
| `CAMPAIGN_TYPE_LABEL` | VARCHAR | 'Personalized' (TypeA), 'Targeted' (TypeB), 'Mass' (TypeC). |
| `START_DATE` | DATE | Campaign start. |
| `END_DATE` | DATE | Campaign end. |
| `DURATION_DAYS` | INT | Length of campaign. |

---

## fact_campaign_enrollment

### fact_campaign_enrollment Description

A bridge table linking Households to Campaigns. I used this table to define the "Target Control Group" for my Difference-in-Differences attribution math.

### fact_campaign_enrollment Columns

| Column | Data Type | Description |
| :--- | :--- | :--- |
| `DESCRIPTION` | VARCHAR | Campaign ID/Description (Links to dim_campaign). |
| `household_key` | INT | Foreign Key to dim_household. |

---

## dim_calendar

### dim_calendar Description

Standard date dimension for Power BI time intelligence.

### dim_calendar Columns

`Date`, `Year`, `Quarter`, `Month`, `Week`, `Day_of_Week`, `Is_Weekend`

---

## Data Model Relationships

I designed the model following a strict **Star Schema** architecture to optimize the performance. Filters flow from dimension tables down to fact tables.

### Relationship Diagram

- `(1)` = One record (Unique Key)
- `(Many)` = Multiple records (Foreign Key)

`dim_household[household_key]          (1) ──< (Many) fact_transactions[household_key]`
`dim_customer_current[household_key]   (1) ──< (Many) fact_transactions[household_key]`
`dim_product[PRODUCT_ID]               (1) ──< (Many) fact_transactions[PRODUCT_ID]`
`dim_calendar[Date]                    (1) ──< (Many) fact_transactions[DATE]`
`dim_campaign[CAMPAIGN]                (1) ──< (Many) fact_redemptions[CAMPAIGN]`
`dim_household[household_key]          (1) ──< (Many) fact_redemptions[household_key]`
`dim_household[household_key]          (1) ─── (1)    dim_rfm[household_key]`

### Data Quality Summary

| Check | Status | Notes |
| :--- | :--- | :--- |
| **Fuel/Points Removed** | Pass | I removed 25,045 rows (Unit Price < $0.05). |
| **Positive Discounts** | Pass | I removed 36 rows. |
| **Churn Threshold** | Pass | I set the threshold to **30 Days** (7.5x Median Interval). |
| **Orphaned Transactions** | Pass | All Product/Household keys exist in dimensions. |
| **Demographics** | Partial | 68% Unknown (Expected limitation). |
