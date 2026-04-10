from backend.db import load_df, execute
import pandas as pd


def get_budgets(month: str):
    return load_df(
        """
        SELECT month, category, budget, is_recurring
        FROM budgets
        WHERE month=%s
        """,
        (month,)
    )


def add_or_update_budget(month, category, amount, is_recurring):
    execute(
        """
        INSERT INTO budgets (month, category, budget, is_recurring)
        VALUES (%s,%s,%s,%s)
        ON CONFLICT (month, category)
        DO UPDATE SET
            budget = EXCLUDED.budget,
            is_recurring = EXCLUDED.is_recurring
        """,
        (month, category, amount, is_recurring)
    )


def update_budget(month, category, amount, is_recurring):
    execute(
        """
        UPDATE budgets
        SET budget=%s, is_recurring=%s
        WHERE month=%s AND category=%s
        """,
        (amount, is_recurring, month, category)
    )


def delete_budgets(month, categories: list[str]):
    execute(
        """
        DELETE FROM budgets
        WHERE month=%s AND category = ANY(%s)
        """,
        (month, categories)
    )


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