# Loyalty Loop: Customer Lifecycle & Campaign ROI Analytics

![Status](https://img.shields.io/badge/Status-Complete-2A9D8F?style=flat-square)
![Tools](https://img.shields.io/badge/Tools-Python%20|%20SQL%20|%20Power%20BI-1B4965?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-5FA8D3?style=flat-square)

> An enterprise grade portfolio project demonstrating Python data pipeline engineering, statistical analysis, and VertiPaq optimized data architecture.

***

## Business Problem

A retail grocery chain with 2,500 tracked households and 2.5 million transactions faced three critical operational blind spots:

1. **Invisible Churn:** The company used a standard 90 day definition for churn. High velocity shoppers were breaking habits weeks before being flagged, rendering retention campaigns reactive.
2. **Metric Contamination:** Core operational metrics were artificially skewed by the inclusion of non merchandise administrative rows (e.g., fuel and loyalty points).
3. **Cannibalization vs. ROI:** Store operations were executing highly complex personalized campaigns without control group visibility into whether these promotions drove incremental Gross Sales or simply subsidized existing behavior.

***

## The Analytical Engine (Jupyter Notebooks)

Before building the presentation layer, I utilized Python and Pandas to validate all statistical assumptions and cleanse the raw data. The core logic is documented in two primary notebooks:

### 1. 01_EDA_Initial_Exploration.ipynb

* **Objective:** Profile the 2.5 million row transaction log.
* **Execution:** I engineered semantic and economic filters to identify and drop 25,000 contaminated records (Fuel and Points) that were destroying basket metrics. I also audited the data for positive discount anomalies to ensure strict financial governance.

### 2. 02_Churn_Threshold_Analysis.ipynb

* **Objective:** Derive a mathematically sound churn definition.
* **Execution:** I calculated the Inter Purchase Intervals for all households, discovering a median return rate of just 4 days. Using a statistical upper fence, I validated a new 30 Day Churn Threshold. I then wrote custom functions to execute a Strategic RFM segmentation model based strictly on biological shopping cycles.

***

## Key Findings & Business Impact

| Category | Finding & Impact |
| :--- | :--- |
| **Gross Sales Protection** | The 30 day threshold revealed 346 High Value Households sitting in the critical 15 to 30 day intervention window. This represents over **$250,000 in annualized Gross Sales** that can now be proactively targeted. |
| **Marketing Efficiency** | Control group Difference in Differences (DiD) analysis proved that Mass Marketing drove a +14% Net Incremental Lift. Conversely, highly complex Personalized Campaigns resulted in a **negative net lift** (cannibalization), providing the mandate to halt them and save store labor. |
| **Data Integrity** | Eradicating 25,000+ noise records corrected core metrics like Average Basket Value, which had previously been skewed by approximately 15%. |

***

## Technical Approach & Architecture

### Phase 1: ETL & Feature Engineering (Python)

I built a Python pipeline to ingest the raw `.csv` files, apply the economic filters, calculate the Strategic RFM scores, and output a clean, normalized relational model.

### Phase 2: Architectural Pivot & Optimization (Power BI)

* **Version 1.0 Failure:** My initial architecture attempted to track historical status using a dense periodic snapshot fact table. Upon loading, this caused Cartesian product explosions and many to many filter collisions that resulted in inaccuracy and performance issues.
* **Version 2.0 Refactor:** I refactored the Python pipeline to output a `dim_customer_current` dimension table based on the absolute maximum transaction date per household. This enforced a strict 1-to-Many star schema, instantly resolving the Cartesian explosions and dropping UI rendering times to sub second levels.
* **Memory Management:** I utilized the external XMLA endpoint tool Measure Killer to audit the final model, physically removing orphaned DAX measures and unused source columns to minimize memory bloat.

***

## Project Structure

```text
loyalty-loop-dashboard/
├── data/
│   ├── raw/                           # (GitIgnored)
│   ├── processed/                     # Cleaned star schema files
├── notebooks/
│   ├── 01_EDA_Initial_Exploration.ipynb
│   ├── 02_Churn_Threshold_Analysis.ipynb
├── docs/
│   ├── CASE_STUDY.md                  # Executive narrative and engineering process
│   ├── METHODOLOGY.md                 # Statistical justification and control group math
│   ├── DATA_DICTIONARY.md             # Column level definitions
│   ├── DAX_MEASURES.md                # Power BI formula reference
│   └── NARRATIVE_GUIDE.md             # Interview talking points
├── scripts/
│   ├── 01_clean_transactions.py       # Economic and semantic filters
│   ├── 02_build_dimensions.py         # Schema construction
│   ├── 03_calculate_rfm.py            # Strategic Segmentation logic
│   └── 04_build_current_state.py      # Version 2.0 dimensional grain control
└── README.md
```

***

## Setup Instructions

1. **Clone the Repository:**

   ```bash
   git clone [https://github.com/jason.donner/loyalty-loop.git](https://github.com/jason.donner/loyalty-loop.git)
   ```

2. **Install Dependencies:**

   ```bash
   pip install pandas numpy matplotlib seaborn jupyter
   ```

3. **Explore the Notebooks:**

   ```bash
   jupyter notebook notebooks/01_EDA_Initial_Exploration.ipynb
   jupyter notebook notebooks/02_Churn_Threshold_Analysis.ipynb
   ```

4. **Launch Presentation Layer:** Open `Loyalty_Loop_Dashboard_v2.0.pbix` in Power BI Desktop to view the optimized star schema and DAX logic.

***

## Author

**Jason Donner**

* Data Analytics & Operations Management Professional
* Focus: Enterprise Data Architecture, Retail Analytics, System Optimization
