# FinTech Lending Portfolio & Repayment Risk Analytics

## Overview

A Python-based analytics project that evaluates a synthetic lending portfolio, monitors repayment performance, identifies overdue loans, and summarizes delinquency across customer risk segments.

The project demonstrates data cleaning, validation, exploratory analysis, SQL-based data storage, and interactive dashboard development relevant to FinTech lending analytics.

## Business Objectives

- Monitor total loan principal and overdue amounts.
- Measure loan delinquency rates across risk segments.
- Analyze scheduled versus paid repayments over time.
- Identify overdue loans requiring further review.
- Validate data quality before producing analytical reports.

## Technology Stack

- **Python** — analysis and processing
- **Pandas** — data cleaning, transformations, and aggregation
- **NumPy** — synthetic data generation
- **SQLite** — analytical data storage
- **Streamlit** — interactive dashboard
- **Git and GitHub** — version control

## Project Structure

```text
FinTech-Lending-Portfolio-Analytics/
├── data/
│   ├── raw/
│   │   ├── customers.csv
│   │   ├── loans.csv
│   │   └── repayments.csv
│   └── processed/
│       ├── lending_portfolio.db
│       ├── loan_portfolio_summary.csv
│       ├── repayments_analyzed.csv
│       └── risk_segment_summary.csv
├── analyze_portfolio.py
├── app.py
├── generate_data.py
├── requirements.txt
├── .gitignore
└── README.md
```

## Key Analytics

- Loan portfolio summaries
- Repayment and overdue tracking
- Days past due (DPD)
- Delinquency rates by risk segment
- Monthly repayment performance
- Data quality validation
- Loans requiring attention

## Run Locally

1. Clone the repository:

   ```bash
   git clone https://github.com/arjavianup523/FinTech-Lending-Portfolio-Analytics.git
   cd FinTech-Lending-Portfolio-Analytics
   ```

2. Create and activate a Python virtual environment.

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Generate the synthetic datasets:

   ```bash
   python generate_data.py
   ```

5. Run the analysis:

   ```bash
   python analyze_portfolio.py
   ```

6. Launch the dashboard:

   ```bash
   streamlit run app.py
   ```

## Data Disclaimer

This project uses synthetic data for educational and portfolio demonstration purposes. It does not contain real customer or lender records, and its results should not be interpreted as actual lending performance.

## Author

**Arjavi Shetye**

GitHub: [arjavianup523](https://github.com/arjavianup523)
