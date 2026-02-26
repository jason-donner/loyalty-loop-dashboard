# Case Study: Customer Lifecycle & Campaign ROI Analytics

> A professional grade portfolio project demonstrating iterative data architecture, strict data governance, and operational analytics using the Dunnhumby dataset.

## Executive Summary

A retail grocery operation required visibility into customer churn risk and marketing effectiveness but lacked a scalable data architecture to support granular analysis.

The initial data pipeline (Version 1.0) attempted to track historical customer status using a monthly snapshot fact table. Upon loading into the presentation layer, this design failed at scale, causing Cartesian products and filter context collisions. To resolve this, I refactored the Python pipeline to output a strict `dim_customer_current` dimension table (Version 2.0). This architectural pivot eliminated the many to many filter collisions, optimizing the model and enabling precise operational drill throughs.

The resulting optimized Power BI architecture uncovered a $250K+ Gross Sales risk hidden by standard industry churn definitions. Furthermore, by applying rigorous control group methodologies, the analysis disproved the assumption that personalization drives growth. The data revealed that highly complex personalized campaigns cannibalized Gross Sales, resulting in a negative net incremental lift, while standard mass marketing drove the highest positive behavioral change. This provided a mathematically sound mandate to shift marketing spend and reduce operational complexity at the store level.

## Situation

### Business Context

The dataset represents a mid size retail grocery operation with:

* **2,500 tracked households** using loyalty cards.
* **2.5 million line item transactions** over 711 days.
* **30 marketing campaigns** across three execution types (personalized, targeted, mass).
* **A high velocity purchase environment** requiring precise, row level evaluation contexts.

### The Technical & Operational Challenges

The marketing and operations teams (me) faced four interconnected systemic failures:

1. **Architectural Scaling Failures (Version 1.0 to 2.0)**
    * The initial approach to tracking customer status relied on a dense periodic snapshot table.
    * This design could not be supported by the Power BI presentation layer. It caused Cartesian products and filter context collisions, rendering granular analysis impossible and heavily hindering performance. The architecture required a complete refactor to a strict one to many dimensional model.
2. **Invisible Churn Risk**
    * The company used an arbitrary, industry standard 90 day definition for customer churn.
    * High velocity grocery shoppers were breaking habits weeks before being flagged, forcing retention campaigns to be reactive autopsies rather than proactive interventions.
3. **Metric Contamination (The "Fuel" Problem)**
    * Core operational metrics were highly volatile.
    * Financial reporting did not distinguish between true merchandise Gross Sales and administrative adjustments or non merchandise transactions (e.g., fuel, loyalty points).
4. **Cannibalization vs. Incremental Lift**
    * Stakeholders lacked control group visibility into campaign ROI.
    * The business operated under the unverified assumption that high complexity personalized marketing was outperforming mass marketing, with no mechanism to confirm this assumption.

### Stakeholder Needs

| Stakeholder | Primary Question |
| :--- | :--- |
| **CMO** | "Which campaigns drive true incremental lift, and which are simply subsidizing normal behavior or cannibalizing sales?" |
| **VP Customer Success** | "When is the intervention window to save a lapsing customer before they are lost?" |
| **Store Operations** | "Does the labor required for complex, personalized campaigns yield a substaintal better than mass marketing?" |
| **Data Engineering** | "Is the data model optimized to ensure data accuracy and high performance?" |

## Task

### Project Scope

Design and engineer an end to end Power BI analytical application that:

1. **Cleanses the raw dataset** of non merchandise anomalies (e.g., fuel, administrative points) to protect core operational metrics.
2. **Derives a custom churn threshold** based on inter purchase interval statistics rather than arbitrary industry defaults.
3. **Engineers a strict dimensional model** capable of supporting granular, row level evaluation contexts without filter collisions.
4. **Measures campaign effectiveness** using a rigorous Pre/Post control group methodology to calculate net incremental Gross Sales lift.

### Success Criteria

| Metric | Target |
| :--- | :--- |
| **System Performance** | Sub second UI rendering via engine optimization. |
| **Data Integrity** | Complete removal of positive discounts and non merchandise rows. |
| **Business Logic** | Churn definitions mathematically anchored to reflect observed purchase cycles. |

## Action

### Phase 1: Data Discovery & Cleansing

I initiated the project by profiling the raw 2.5 million row transaction log using Python and Pandas. While high level summary statistics appeared normal, granular row analysis revealed critical anomalies that would invalidate all downstream DAX calculations.

**Discovery 1: The Fuel & Points Contamination**
I isolated transactions with massive unit quantities (over 10,000) but negligible Gross Sales (under $5.00).

* **Root Cause:** Fuel purchases (measured in gallons) and "Loyalty Points" (administrative entries) were commingled with actual merchandise.
* **Action:** I engineered a Python cleaning pipeline applying a semantic filter (excluding "FUEL" keywords) and an economic filter (excluding items with a Unit Price < $0.05). This purged approximately 25,000 contaminated records.

**Discovery 2: Positive Discounts**
I identified rows containing positive numerical values in the `RETAIL_DISC` column.

* **Root Cause:** Operational surcharges, such as bottle deposits and bag fees, were mapped incorrectly.
* **Action:** I purged these rows to prevent the artificial inflation of promotional ROI metrics.

### Phase 2: Architectural Pivot (Version 1.0 to Version 2.0)

**The Version 1.0 Failure:**
Stakeholders required historical visibility into customer churn. My initial architecture generated a `fact_monthly_snapshots` table in Python to track every customer's status at every month end. However, when loaded into the Power BI presentation layer, this dense snapshot fact table caused severe many to many filter context collisions. Attempting to cross filter this table against transaction data resulted in inaccuracies, rendering micro level drill throughs impossible and breaking data integrity rules.

**The Version 2.0 Refactor:**
I abandoned the snapshot approach and refactored the Python ETL pipeline to output a strict `dim_customer_current` dimension table.

* **Execution:** The script now isolates the absolute maximum transaction date per household and calculates `Current_Status` and `Current_Lapsed_Days` as static attributes.
* **Impact:** This enforced a strict one to many star schema, instantly resolving the Cartesian products, eliminating DAX ambiguity, and dropping dashboard load times to sub second levels.

### Phase 3: Marketing Science & Feature Engineering

**1. Defining "Churn" with Statistics**
I tested the industry standard 90 day churn assumption by calculating the Inter Purchase Intervals for every household.

* **Finding:** The median customer returned every 4 days. Waiting 90 days meant waiting 22 times the typical cycle.
* **Execution:** I set the Churn Threshold at 30 days (capturing 90% of all return behavior) to create a highly actionable "Intervention Window" between days 15 and 30.

**2. Strategic RFM Segmentation**
Standard RFM quintiles failed because they ignored the 30 day threshold. I engineered a Strategic RFM model where the Recency score was hard coded to the operational business cycles (e.g., a Score of 3 strictly equals the 15 to 30 day At Risk window), ensuring segments were actionable rather than purely mathematical.

**3. Control Group Campaign Attribution**
To measure true ROI, I deployed a Difference in Differences (DiD) methodology, comparing the 30 day pre and post Gross Sales behavior of coupon redeemers against a control group of non redeemers.

| Campaign Type | Net Incremental Lift | Operational Insight |
| :--- | :--- | :--- |
| **Mass (Type C)** | **+14%** | **Optimal execution.** Drove the highest positive behavioral change at scale. |
| **Targeted (Type B)** | +6% | Moderate impact. |
| **Personalized (Type A)** | **Negative** | **Failed execution.** High operational complexity (Promoted SKUs) resulted in Gross Sales cannibalization rather than incremental lift. |

### Phase 4: Performance Optimization

A portfolio piece is incomplete without strict resource management. I utilized an external XMLA endpoint diagnostic tool (Measure Killer) to audit the data model.

* I identified and physically deleted orphaned DAX measures (relics from the Version 1.0 snapshot architecture).
* I removed unused columns at the Power Query source level, drastically reducing the memory footprint of the database and optimizing the final deliverable for enterprise deplodyment.

## Result

### Quantified Business Impact

1. **Gross Sales Preservation:** The implementation of the 30 day churn threshold identified 346 High Value Households sitting in the critical "Risk Zone" (15 to 30 days inactive). This cohort represented over $250,000 in annualized Gross Sales. The business can now deploy proactive retention interventions before these habits are permanently broken.
2. **Strategic Marketing Reallocation:** The control group analysis dismantled the assumption that personalization inherently drives growth. The data proved that Mass Campaigns (Type C) generated the highest Net Incremental Lift (+14%). Conversely, highly complex Personalized Campaigns (Type A) cannibalized Gross Sales, resulting in a negative net lift. This provided a mathematically sound mandate to halt personalized efforts, saving the company both marketing budget and the heavy store level labor required to execute high complexity promotions.
3. **Data Integrity and Governance:** The Python cleaning pipeline eradicated 25,000+ non merchandise noise records (e.g., fuel and points). This corrected core operational metrics, such as Average Basket Value, which had previously been skewed by approximately 15% due to the inclusion of low value point redemptions.

### Lessons Learned

* **Averages Mask Reality:** The mean inter purchase interval (7.3 days) completely hid the true high frequency behavior of the customer base (Median 4.0 days). Relying on summary statistics without plotting the distribution curve leads to catastrophic business assumptions.
* **Complexity Does Not Equal ROI:**  The "Promoted SKUs" metric revealed that highly complex campaigns require significant physical labor to execute at the store level but do not guarantee financial returns. Evaluating operational effort against true behavioral lift is mandatory.
* **Architecture Dictates Performance:** The initial attempt to model historical churn using a dense periodic snapshot table (Version 1.0) proved that raw data dumps cause substaintal performance and quality issues. Transforming the pipeline to output a strict `dim_customer_current` dimension table (Version 2.0) reinforced that high dashboard performance is won or lost in the ETL and data modeling layers, not the UI layer.
