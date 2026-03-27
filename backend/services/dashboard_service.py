from backend.services.income_service import get_all_income
from backend.services.expense_service import get_all_expenses


def get_dashboard_summary(month: str):
    income_df = get_all_income()
    expense_df = get_all_expenses()

    income_total = income_df[income_df["Month"] == month]["amount"].sum()
    expense_total = expense_df[expense_df["Month"] == month]["amount"].sum()

    balance = income_total - expense_total

    return {
        "month": month,
        "income_total": float(income_total),
        "expense_total": float(expense_total),
        "balance": float(balance),
    }