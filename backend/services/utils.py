import pandas as pd
from backend.db import load_df, execute


def auto_apply_recurring_income(income_df, target_month):
    """
    Auto-inserts recurring income for the given month if missing.
    Returns list of sources that were auto-added.
    """
    recurring = income_df[income_df["income_type"] == "Recurring"]

    if recurring.empty:
        return []

    added = []

    for _, r in recurring.iterrows():
        exists = income_df[
            (income_df["Month"] == target_month) &
            (income_df["source"] == r["source"]) &
            (income_df["category"] == r["category"])
        ]

        if exists.empty:
            execute(
                """INSERT INTO income
                   (date, source, category, amount, income_type)
                   VALUES (%s,%s,%s,%s,'Recurring')""",
                (
                    pd.to_datetime(f"{target_month}-01"),
                    r["source"],
                    r["category"],
                    r["amount"]
                )
            )
            added.append(r["source"])

    return added

def auto_apply_recurring(expense_df, target_month):
    """
    Auto-inserts recurring expenses for the given month if missing.
    Returns list of names that were auto-added.
    """
    recurring = expense_df[expense_df["expense_type"] == "Recurring"]

    if recurring.empty:
        return []

    added = []

    for _, r in recurring.iterrows():
        exists = expense_df[
            (expense_df["Month"] == target_month) &
            (expense_df["name"] == r["name"]) &
            (expense_df["category"] == r["category"])
        ]

        if exists.empty:
            execute(
                """INSERT INTO expenses
                   (date, name, category, amount, payment_method, expense_type)
                   VALUES (%s,%s,%s,%s,%s,'Recurring')""",
                (
                    pd.to_datetime(f"{target_month}-01"),
                    r["name"],
                    r["category"],
                    r["amount"],
                    r["payment_method"]
                )
            )
            added.append(r["name"])

    return added

def auto_apply_recurring_budgets(target_month):
    target_period = pd.Period(target_month, freq="M")
    prev_month = str(target_period - 1)

    prev_budgets = load_df(
        """
        SELECT category, budget
        FROM budgets
        WHERE month=%s AND is_recurring = TRUE
        """,
        (prev_month,)
    )

    if prev_budgets.empty:
        return []

    current = load_df(
        "SELECT category FROM budgets WHERE month=%s",
        (target_month,)
    )

    existing = set(current["category"])
    added = []

    for _, r in prev_budgets.iterrows():
        if r["category"] not in existing:
            execute(
                """
                INSERT INTO budgets (month, category, budget, is_recurring)
                VALUES (%s,%s,%s,TRUE)
                """,
                (target_month, r["category"], r["budget"])
            )
            added.append(r["category"])

    return added
