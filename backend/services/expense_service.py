import pandas as pd
from db import load_df, execute


def get_all_expenses():
    df = load_df("SELECT * FROM expenses ORDER BY date DESC")

    if df.empty:
        df["Month"] = []
        return df

    df["date"] = pd.to_datetime(df["date"], format="mixed")
    df["Month"] = df["date"].dt.to_period("M").astype(str)
    return df


def add_expense(date, name, category, amount, payment_method, expense_type):
    execute(
        """
        INSERT INTO expenses
        (date, name, category, amount, payment_method, expense_type)
        VALUES (%s,%s,%s,%s,%s,%s)
        """,
        (date, name, category, amount, payment_method, expense_type)
    )


def update_expense(id, date, name, category, amount, payment_method):
    execute(
        """
        UPDATE expenses
        SET date=%s, name=%s, category=%s,
            amount=%s, payment_method=%s
        WHERE id=%s
        """,
        (date, name, category, amount, payment_method, id)
    )


def delete_expenses(ids: list[int]):
    execute(
        "DELETE FROM expenses WHERE id = ANY(%s)",
        (ids,)
    )


def auto_apply_recurring_expenses(expense_df, target_month):
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
                """
                INSERT INTO expenses
                (date, name, category, amount, payment_method, expense_type)
                VALUES (%s,%s,%s,%s,%s,'Recurring')
                """,
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