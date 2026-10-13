from pathlib import Path
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data" / "processed"

st.set_page_config(page_title="Lending Risk Analytics", layout="wide")
st.title("FinTech Lending Portfolio & Risk Analytics")
st.caption("Synthetic data | Reporting date: 13 October 2026")

loan_file = DATA / "loan_portfolio_summary.csv"
repayment_file = DATA / "repayments_analyzed.csv"

if not loan_file.exists() or not repayment_file.exists():
    st.error("Processed reports are missing.")
    st.write("Project folder:", str(ROOT))
    st.write("Expected reports folder:", str(DATA))
    st.write("Run generate_data.py and analyze_portfolio.py first.")
    st.stop()

loans = pd.read_csv(loan_file)
repayments = pd.read_csv(repayment_file)

st.sidebar.header("Filters")
segments = sorted(loans["risk_segment"].dropna().unique())
selected = st.sidebar.multiselect("Risk segment", segments, default=segments)
loans = loans[loans["risk_segment"].isin(selected)]

repayments["due_date"] = pd.to_datetime(repayments["due_date"], errors="coerce")
repayments = repayments[
    (repayments["due_date"] <= pd.Timestamp("2026-10-13"))
    & repayments["loan_id"].isin(loans["loan_id"])
]

count = loans["loan_id"].nunique()
principal = loans["loan_amount"].sum()
overdue = loans["overdue_amount"].sum()
delinquent = loans["is_delinquent"].sum()
rate = delinquent / count * 100 if count else 0

a, b, c, d = st.columns(4)
a.metric("Total loans", f"{count:,}")
b.metric("Loan principal", f"₹{principal:,.0f}")
c.metric("Overdue amount", f"₹{overdue:,.0f}")
d.metric("Delinquency rate", f"{rate:.2f}%")

st.subheader("Risk segment analysis")
if not loans.empty:
    summary = loans.groupby("risk_segment").agg(
        Loans=("loan_id", "nunique"),
        Delinquent_Loans=("is_delinquent", "sum"),
        Overdue_Amount=("overdue_amount", "sum"),
    )
    summary["Delinquency_Rate_Pct"] = (
        100 * summary["Delinquent_Loans"] / summary["Loans"]
    ).round(2)

    left, right = st.columns(2)
    with left:
        st.bar_chart(summary[["Loans"]])
    with right:
        st.bar_chart(summary[["Overdue_Amount"]])
    st.dataframe(summary, use_container_width=True)

st.subheader("Monthly repayment performance")
if not repayments.empty:
    repayments["month"] = repayments["due_date"].dt.to_period("M").astype(str)
    monthly = repayments.groupby("month").agg(
        Amount_Due=("amount_due", "sum"),
        Amount_Paid=("amount_paid", "sum"),
    )
    st.line_chart(monthly[["Amount_Due", "Amount_Paid"]])
    st.dataframe(monthly.round(2), use_container_width=True)

st.subheader("Loans requiring attention")
overdue_loans = loans[loans["overdue_amount"] > 0].sort_values(
    ["max_dpd", "overdue_amount"], ascending=False
)
columns = [
    "loan_id", "customer_id", "risk_segment", "loan_amount",
    "overdue_amount", "max_dpd", "overdue_installments"
]
st.dataframe(overdue_loans[columns].head(20), use_container_width=True)

st.download_button(
    "Download loan report",
    data=loans.to_csv(index=False).encode("utf-8"),
    file_name="loan_portfolio_report.csv",
    mime="text/csv",
)

st.caption(
    "All records are synthetic. Overdue amounts are unpaid overdue "
    "installments, not remaining loan principal."
)
