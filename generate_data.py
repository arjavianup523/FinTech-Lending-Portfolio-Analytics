from pathlib import Path
import numpy as np
import pandas as pd

rng = np.random.default_rng(42)
out = Path("data") / "raw"
out.mkdir(parents=True, exist_ok=True)

as_of_date = pd.Timestamp("2026-10-13")
n_customers = 1200
n_loans = 1800

# Generate customers
customer_ids = [f"CUST{i:05d}" for i in range(1, n_customers + 1)]

customers = pd.DataFrame({
    "customer_id": customer_ids,
    "monthly_income": rng.integers(15000, 200001, n_customers),
    "credit_score": rng.integers(300, 851, n_customers),
    "employment_type": rng.choice(
        ["Salaried", "Self-employed", "Contract", "Unemployed"],
        n_customers,
        p=[0.55, 0.25, 0.15, 0.05]
    ),
    "region": rng.choice(
        ["West", "North", "South", "East", "Central"],
        n_customers
    )
})

customers["risk_segment"] = pd.cut(
    customers["credit_score"],
    bins=[299, 579, 669, 850],
    labels=["High Risk", "Medium Risk", "Low Risk"]
).astype(str)

# Generate loans
start = pd.Timestamp("2024-01-01").timestamp()
end = pd.Timestamp("2026-07-01").timestamp()

loans = pd.DataFrame({
    "loan_id": [f"LOAN{i:05d}" for i in range(1, n_loans + 1)],
    "customer_id": rng.choice(customer_ids, n_loans),
    "loan_amount": rng.integers(5000, 200001, n_loans),
    "interest_rate_pct": np.round(rng.uniform(10, 36, n_loans), 2),
    "loan_term_months": rng.choice([3, 6, 9, 12], n_loans),
    "loan_date": pd.to_datetime(
        rng.integers(int(start), int(end), n_loans), unit="s"
    ).normalize()
})

score_map = customers.set_index("customer_id")["credit_score"]
loan_scores = loans["customer_id"].map(score_map)

loans["interest_rate_pct"] = np.round(
    np.clip(
        loans["interest_rate_pct"] + (700 - loan_scores) * 0.025,
        8, 40
    ), 2
)

loans["total_repayment"] = np.round(
    loans["loan_amount"] * (
        1 + loans["interest_rate_pct"] / 100
        * loans["loan_term_months"] / 12
    ), 2
)

# Generate installment-level repayment records
records = []

for loan in loans.itertuples(index=False):
    regular_amount = round(
        loan.total_repayment / loan.loan_term_months, 2
    )
    score = int(score_map[loan.customer_id])

    for installment in range(1, loan.loan_term_months + 1):
        due_date = loan.loan_date + pd.DateOffset(months=installment)

        amount_due = (
            round(loan.total_repayment - regular_amount
                  * (loan.loan_term_months - 1), 2)
            if installment == loan.loan_term_months
            else regular_amount
        )

        amount_paid = 0.0
        payment_date = pd.NaT

        if due_date <= as_of_date:
            paid_probability = float(np.clip(
                0.88 - (650 - score) / 1000, 0.65, 0.93
            ))
            outcome = rng.random()

            if outcome < paid_probability:
                amount_paid = amount_due
                days_available = (as_of_date - due_date).days
                delay = int(rng.integers(
                    0, min(30, days_available) + 1
                ))
                payment_date = due_date + pd.Timedelta(days=delay)

            elif outcome < paid_probability + 0.08:
                amount_paid = round(
                    amount_due * rng.uniform(0.1, 0.85), 2
                )
                payment_date = due_date

        records.append({
            "repayment_id": f"REP{len(records) + 1:07d}",
            "loan_id": loan.loan_id,
            "installment_number": installment,
            "due_date": due_date,
            "amount_due": amount_due,
            "amount_paid": amount_paid,
            "payment_date": payment_date
        })

repayments = pd.DataFrame(records)

customers.to_csv(out / "customers.csv", index=False)
loans.to_csv(out / "loans.csv", index=False)
repayments.to_csv(out / "repayments.csv", index=False)

print("DATA GENERATION COMPLETE")
print(f"Customers: {len(customers):,}")
print(f"Loans: {len(loans):,}")
print(f"Repayment records: {len(repayments):,}")
print(f"Files saved to: {out.resolve()}")
