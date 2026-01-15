# Data Quality Log

## Issue 1: Positive Discounts
- **Date Found:** [Date]
- **Table:** transaction_data
- **Columns:** RETAIL_DISC, COUPON_DISC
- **Count:** 36 rows
- **Root Cause:** Operational surcharges (bottle deposits, bag fees)
- **Resolution:** Remove from analysis
- **Impact:** Prevents ROAS contamination

## Issue 2: Missing Demographics
- **Date Found:** [Date]
- **Table:** hh_demographic
- **Issue:** Only 801 of 2,500 households have data (32%)
- **Resolution:** Fill missing with 'Unknown'
- **Impact:** Segment analysis limited to known households