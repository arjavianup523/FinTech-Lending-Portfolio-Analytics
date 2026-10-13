from pathlib import Path
import sqlite3
import pandas as pd

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "processed"
OUT.mkdir(parents=True, exist_ok=True)
AS_OF_DATE = pd.Timestamp("2026-10-13")

required = ["customers.csv", "loans.csv", "repayments.csv"]
missing = [name for name in required if not (RAW / name).exists()]

if missing:
    raise FileNotFoundError(
        f"Missing input files: {missing}. "
        "Create the datasets first using generate_data.py."
    )

customers = pd.read_csv(RAW / "customers.csv")
loans = pd.read_csv(RAW / "loans.csv")
repayments = pd.read_csv(RAW / "repayments.csv")

for col in ["loan_date"]:
    loans[col] = pd.to_datetime(loans[col])

for col in ["due_date", "payment_date"]:
    repayments[col] = pd.to_datetime(repayments[col], errors="coerce")

# Data quality checks
checks = {
    "Duplicate customer IDs": customers["customer_id"].duplicated().sum(),
    "Duplicate loan IDs": loans["loan_id"].duplicated().sum(),
    "Duplicate repayment IDs": repayments["repayment_id"].duplicated().sum(),
    "Loans with unknown customers": (
        ~loans["customer_id"].isin(customers["customer_id"])
    ).sum(),
    "Repayments with unknown loans": (
        ~repayments["loan_id"].isin(loans["loan_id"])
    ).sum(),
    "Negative amounts due": (repayments["amount_due"] < 0).sum(),
    "Negative amounts paid": (repayments["amount_paid"] < 0).sum(),
    "Payments above amount due": (
        repayments["amount_paid"] > repayments["amount_due"]
    ).sum(),
}

print("\nDATA QUALITY CHECKS")
for name, count in checks.items():
    print(f"{name}: {count}")

if any(checks.values()):
    raise ValueError("Data quality checks failed. Fix these before analysis.")

# Installment-level calculations
repayments["outstanding_amount"] = (
    repayments["amount_due"] - repayments["amount_paid"]
).clip(lower=0).round(2)

repayments["days_past_due"] = (
    AS_OF_DATE - repayments["due_date"]
).dt.days.clip(lower=0)

repayments["is_overdue"] = (
    (repayments["due_date"] < AS_OF_DATE)
    & (repayments["outstanding_amount"] > 0)
)

repayments.loc[~repayments["is_overdue"], "days_past_due"] = 0

repayments["repayment_status"] = "Upcoming"
repayments.loc[
    (repayments["due_date"] <= AS_OF_DATE)
    & (repayments["outstanding_amount"] == 0),
    "repayment_status"
] = "Paid"
repayments.loc[
    repayments["is_overdue"], "repayment_status"
] = "Overdue"
repayments.loc[
    repayments["is_overdue"] & (repayments["amount_paid"] > 0),
    "repayment_status"
] = "Partially Paid - Overdue"
repayments.loc[
    repayments["due_date"] == AS_OF_DATE,
    "repayment_status"
] = "Due Today"

# Restrict due-to-date balances to installments due by the reporting date
repayments["due_by_report_date"] = (
    repayments["due_date"] <= AS_OF_DATE
)
repayments["balance_due_to_date"] = (
    repayments["outstanding_amount"]
    * repayments["due_by_report_date"].astype(int)
)
repayments["overdue_amount"] = (
    repayments["outstanding_amount"]
    * repayments["is_overdue"].astype(int)
)

loan_summary = repayments.groupby("loan_id").agg(
    scheduled_repayment=("amount_due", "sum"),
    installments_due=("due_by_report_date", "sum"),
    amount_paid=("amount_paid", "sum"),
    outstanding_due_to_date=("balance_due_to_date", "sum"),
    overdue_amount=("overdue_amount", "sum"),
    overdue_installments=("is_overdue", "sum"),
    max_dpd=("days_past_due", "max"),
).reset_index()

# Attach loan and customer information
loan_summary = loans.merge(loan_summary, on="loan_id", how="left")
loan_summary = loan_summary.merge(
    customers[["customer_id", "credit_score", "risk_segment"]],
    on="customer_id",
    how="left",
)
loan_summary["is_delinquent"] = (
    loan_summary["overdue_installments"] > 0
).astype(int)

# Risk-segment reporting
risk_summary = loan_summary.groupby(
    "risk_segment", dropna=False
).agg(
    number_of_loans=("loan_id", "nunique"),
    overdue_loans=("is_delinquent", "sum"),
    total_loan_principal=("loan_amount", "sum"),
    overdue_amount=("overdue_amount", "sum"),
    outstanding_due_to_date=("outstanding_due_to_date", "sum"),
).reset_index()

risk_summary["delinquency_rate_pct"] = (
    100 * risk_summary["overdue_loans"]
    / risk_summary["number_of_loans"].replace(0, pd.NA)
).round(2)

# Export reports
repayments.to_csv(OUT / "repayments_analyzed.csv", index=False)
loan_summary.to_csv(OUT / "loan_portfolio_summary.csv", index=False)
risk_summary.to_csv(OUT / "risk_segment_summary.csv", index=False)

# Create a local SQL database
with sqlite3.connect(OUT / "lending_portfolio.db") as conn:
    customers.to_sql("customers", conn, if_exists="replace", index=False)
    loans.to_sql("loans", conn, if_exists="replace", index=False)
    repayments.to_sql(
        "repayments_analyzed", conn, if_exists="replace", index=False
    )
    loan_summary.to_sql(
        "loan_portfolio_summary", conn, if_exists="replace", index=False
    )

print("\nPORTFOLIO ANALYSIS COMPLETE")
print(f"Reporting date: {AS_OF_DATE.date()}")
print(f"Processed files saved in: {OUT}")
print("\nRISK SEGMENT SUMMARY")
print(risk_summary.to_string(index=False))
