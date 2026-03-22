# Shopee Regional Brand & Revenue Analytics (PH, MY, TH)

## 📌 Project Overview
This project addresses the challenge of fragmented e-commerce data in the Southeast Asian (SEA) beauty market. Using raw listing data from Shopee across the **Philippines (PH)**, **Malaysia (MY)**, and **Thailand (TH)**, I built a pipeline to clean and analyze brand performance across different regulatory and linguistic environments.

### Key Objectives:
* **Market Alignment:** Standardize disparate listing titles across three distinct countries.
* **Fuzzy Matching:** Implement fuzzy string matching to identify global brands within messy, localized raw data.
* **Competitive Intelligence:** Compare regional revenue and units sold to identify well-performing and brands with high-growth potential.

---

## 🛠️ Technical Stack
* **Language:** Python 3.x
* **Libraries:** `Pandas` (Data manipulation), `RapidFuzz` (Fuzzy matching), `Unidecode` (Linguistic normalization)
* **CLI Tooling:** `Argparse`
* **Visualization:** RMarkdown / Power BI

---

## 🌟 Feature Highlights

### 1. Scalable Fuzzy Matching Logic
Utilized `RapidFuzz` to implement a multi-view scoring system that handles the "noise" of marketplace listings:
* **Partial Ratio:** Detects brand names buried inside long, descriptive titles.
* **Token Set Ratio:** Accounts for different word orders (e.g., "Brand X Serum" vs "Serum Brand X").
* **Score Thresholding:** Tunable acceptance threshold (default 85%) to ensure high data integrity for C-suite reporting.

### 2. Automated Revenue Aggregation
The pipeline (`aggregate_country_basic.py`) automates the calculation of **Revenue (USD)** by coercing localized currency/unit formats into numeric types, generating two strategic views:
* **Brand Summary:** Aggregated performance for regional benchmarking.
* **Shop x Brand View:** Identifying "Grey Market" vs. Official Store performance—crucial for **Ecosystem Governance**.

---

## 📂 Development Setup & Usage Guide

Follow these steps to configure your local environment and process raw marketplace data.

### 1. Prerequisites
Ensure you have the following installed on your system:
* [**Python 3.9+**](https://www.python.org/downloads/) - Core programming language.
* [**pip**](https://pip.pypa.io/en/stable/installation/) - Python’s package installer.
* [**Git**](https://git-scm.com/downloads) - To clone the repository.

### 2. Installation
```sh
# Clone the repository
git clone https://github.com/Blerber/shopee-regional-analysis.git
cd shopee-regional-analysis

# Install dependencies
pip install pandas rapidfuzz unidecode

# Set up folder structure
mkdir -p data/raw data/brands data/processed data/summary scripts
```

### 3. Running the Pipeline
The analysis is split into two sequential stages: **Matching** and **Aggregation**.

#### **Step A: Brand Matching**
This script identifies brands in messy listing titles using fuzzy logic.
```sh
python scripts/match_listing_to_brands.py \
  data/raw/shopee_malaysia_raw.csv \
  data/brands/brands_master.csv \
  data/processed/my_matched.csv \
  --threshold 85
```

#### **Step B: Data Aggregation**
This script calculates financial metrics and flags "unmatched" items for manual audit.
```sh
python scripts/aggregate_country_basic.py \
  data/processed/my_matched.csv \
  data/summary/my_brand_report.csv \
  data/summary/my_shop_performance.csv \
  data/summary/my_unmatched_audit.csv
```

---

## 🛡️ Troubleshooting & Data Integrity

### **Handling "No Brand" Results**
If a large volume of data falls into `unmatched_audit.csv`, follow these steps:
1.  **Low Threshold:** If brands are spelled correctly but not matching, lower the `--threshold` to `75` in Step A.
2.  **Linguistic Variations:** Add local language variations (e.g., Thai script) to `data/brands/brands_master.csv`.
3.  **Character Encoding:** Ensure raw data is saved in **UTF-8** format to support international characters.
