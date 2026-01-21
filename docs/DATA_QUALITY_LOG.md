# Data Quality Log
>
> Tracking anomalies, cleaning decisions, and transformation logic.

---

## Issue 1: Positive Discounts (Operational Surcharges)

- **Date Found:** 2024-01-15
- **Table:** `transaction_data`
- **Columns:** `RETAIL_DISC`, `COUPON_DISC`
- **Severity:** High (Financial Accuracy)
- **Observation:** 36 rows contained positive values in discount columns, which implies a price *increase* rather than a deduction.
- **Root Cause:** Analysis of product descriptions linked these rows to "BOTTLE DEPOSITS" and "BAG FEES" — operational surcharges incorrectly mapped to discount fields.
- **Impact:** Including these would systematically underreport marketing spend and contaminate ROAS calculations.
- **Resolution:** Removed all rows where `RETAIL_DISC > 0` or `COUPON_DISC > 0`.
- **Rows Affected:** 36

## Issue 2: Non-Merchandise Contamination (Fuel)

- **Date Found:** 2024-01-15
- **Table:** `transaction_data`
- **Columns:** `COMMODITY_DESC`
- **Severity:** Critical (Metric Distortion)
- **Observation:** Found distinct product IDs with quantities > 10,000 but low sales value.
- **Root Cause:** Fuel purchases were included in the dataset. "Quantity" for fuel likely represents milliliters or gallons, not distinct retail units.
- **Impact:** Destroyed "Average Units per Basket" and "Average Unit Price" metrics (e.g., a single visit appearing to have 15,000 items).
- **Resolution:** Removed rows where `COMMODITY_DESC` contains "FUEL" or "GASOLINE".
- **Rows Affected:** Part of the ~25k non-merchandise block.

## Issue 3: Administrative Line Items (Points/Tokens)

- **Date Found:** 2024-01-15
- **Table:** `transaction_data`
- **Columns:** `SALES_VALUE`, `QUANTITY`
- **Severity:** Critical (Metric Distortion)
- **Observation:** Large volume of transactions with extremely low unit prices (e.g., $0.002/unit).
- **Root Cause:** Loyalty program accounting entries (e.g., "100 Points") logged as transaction line items.
- **Impact:** Inflates transaction volume and depresses average unit price.
- **Resolution:** Implemented an **Economic Filter**: Removed rows where implied `Unit Price < $0.05` AND `Sales Value > 0`.
- **Rows Affected:** ~25,000 (Combined with Fuel).

## Issue 4: Extreme Quantity Outliers (Fat-Finger Errors)

- **Date Found:** 2024-01-15
- **Table:** `transaction_data`
- **Columns:** `QUANTITY`
- **Severity:** Medium
- **Observation:** Valid grocery items (e.g., Candy, Corn) showing quantities > 150 in a single scan.
- **Root Cause:** Likely cashier entry errors ("fat-finger") or B2B bulk transfers not representative of consumer behavior.
- **Impact:** Skews "Max Quantity" statistics and basket size analysis.
- **Resolution:** Applied a **Safety Cap**: Removed rows where `QUANTITY > 150`.
- **Rows Affected:** Minimal (< 100 rows).

## Issue 5: Missing Demographics

- **Date Found:** 2024-01-16
- **Table:** `hh_demographic`
- **Columns:** All demographic fields
- **Severity:** Medium (Segmentation Limit)
- **Observation:** Demographic data exists for only 801 of 2,500 households (32% coverage).
- **Root Cause:** Voluntary data submission (likely from loyalty signup forms) or legacy data gaps.
- **Impact:** Cannot perform demographic profiling (Age/Income) on 68% of the customer base.
- **Resolution:** Performed a `LEFT JOIN` keeping all transactions. Filled missing demographic fields with `'Unknown'` to preserve the "Shadow Customer" segment in financial reporting.
- **Rows Affected:** 1,699 Households.

## Issue 6: Relative Date Format

- **Date Found:** 2024-01-15
- **Table:** `transaction_data`
- **Columns:** `DAY`
- **Severity:** Low (Usability)
- **Observation:** Dates provided as integers (1-711) rather than calendar dates.
- **Impact:** Prevents standard time-series analysis (Seasonality, MoM, YoY) in Power BI.
- **Resolution:** Anchored `Day 1` to `2024-01-01` and calculated absolute dates for all records.