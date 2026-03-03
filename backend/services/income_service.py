import pandas as pd
from db import load_df, execute


def get_all_income():
    df = load_df("SELECT * FROM income ORDER BY date DESC")

    if df.empty:
        df["Month"] = []
        return df

    df["date"] = pd.to_datetime(df["date"], format="mixed")
    df["Month"] = df["date"].dt.to_period("M").astype(str)
    return df


def add_income(date, source, category, amount, income_type):
    execute(
        """
        INSERT INTO income (date, source, category, amount, income_type)
        VALUES (%s,%s,%s,%s,%s)
        """,
        (date, source, category, amount, income_type)
    )


def update_income(id, date, source, category, amount):
    execute(
        """
        UPDATE income
        SET date=%s, source=%s, category=%s, amount=%s
        WHERE id=%s
        """,
        (date, source, category, amount, id)
    )


def delete_income(ids: list[int]):
    execute(
        "DELETE FROM income WHERE id = ANY(%s)",
        (ids,)
    )


def auto_apply_recurring_income(income_df, target_month):
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
                """
                INSERT INTO income
                (date, source, category, amount, income_type)
                VALUES (%s,%s,%s,%s,'Recurring')
                """,
                (
                    pd.to_datetime(f"{target_month}-01"),
                    r["source"],
                    r["category"],
                    r["amount"]
                )
            )
            added.append(r["source"])

    return added