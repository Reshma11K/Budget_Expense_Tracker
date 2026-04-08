# ==============================
# IMPORTS & APP SETUP
# ==============================
import streamlit as st
import pandas as pd
from datetime import date
from backend.db import load_df, execute
import matplotlib.pyplot as plt

import requests

API_URL = "http://127.0.0.1:8000"


from backend.services.income_service import (
    get_all_income,
)

from backend.services.expense_service import (
    get_all_expenses,
    auto_apply_recurring_expenses,
)

from backend.services.budget_service import (
    get_budgets_for_month,
    update_budget,
    delete_budgets,
)

plt.rcParams.update({
    "figure.facecolor": "#111111",
    "axes.facecolor": "#1a1a1a",
    "axes.edgecolor": "#333333",
    "axes.labelcolor": "#dddddd",
    "text.color": "#e6e6e6",
    "xtick.color": "#bbbbbb",
    "ytick.color": "#bbbbbb",
    "grid.color": "#2a2a2a",
    "legend.facecolor": "#1a1a1a",
    "legend.edgecolor": "#333333",
})

from backend.ui.styles import apply_sidebar_style
from backend.ui.layout import sidebar
apply_sidebar_style()

from backend.ui.filters import apply_expense_filters
from backend.ui.filters import apply_recurring_filters

# ==============================
# DASHBOARD COLOR PALETTE
# ==============================
COLORS = {
    "budget": "#6b7280",     # muted gray
    "actual_ok": "#3b82f6",  # muted blue
    "actual_bad": "#ef4444", # muted red
    "income": "#22c55e",     # muted green
    "expense": "#f97316",    # muted orange
    "grid": "#374151",       # dark gray
    "bg": "#1f2933"
}


# ==============================
# 🔐 LOGIN BLOCK (PUT HERE)
# ==============================
if "token" not in st.session_state:
    st.session_state["token"] = None

if not st.session_state["token"]:
    st.title("🔐 Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        r = requests.post(
            f"{API_URL}/login",
            json={"username": username, "password": password}
        )

        print("STATUS:", r.status_code)
        print("RAW RESPONSE:", r.text)

        try:
            data = r.json()
        except Exception:
            st.error(f"Login failed: {r.text}")
            st.stop()

        if data and "access_token" in data:
            st.session_state["token"] = data["access_token"]
            st.rerun()
        else:
            st.error("Invalid credentials")

    st.stop()  # 🚨 VERY IMPORTANT


# ==============================
# TABS
# ==============================
menu = sidebar()

# ==============================
# NORMAL APP STARTS HERE
# ==============================

st.set_page_config(page_title="Household Budget App", layout="wide")
st.title("🏠 Household Budget App")
st.caption("Track. Control. Grow our money. HeHeHeeeeeeeee")
st.divider()
# ==============================
# CONSTANTS
# ==============================
INCOME_CATEGORIES = ["Salary", "Bonus", "Edenred", "Investments", "Other"]

EXPENSE_CATEGORIES = [
    "Grocery/Utilities", "Credit Cards", "India", "Transport",
    "Foodgasm", "Wants/Need", "Entertainment", "Emergency",
    "Invest", "Savings", "Travel", "Gifts", "Others"
]

RECURRING_CATEGORIES = [
    "Rent", "Transport", "Internet", "Mobile charges", "Electricity",
    "Insurance", "Scalable Savings", "Other"
]

PAYMENT_METHODS = [
    "Cash", "Bank Transfer", "N26 V", "N26 R",
    "Edenred", "Amex", "Gebührenfrei", "Trade Republic"
]

# ==============================
# BUDGET CATEGORIES (VARIABLE + RECURRING)
BUDGET_CATEGORIES = sorted(
    set(EXPENSE_CATEGORIES + RECURRING_CATEGORIES)
)


# ==============================
# LOADERS (FIXED DATE PARSING)
# ==============================
def auth_headers():
    return {
        "Authorization": f"Bearer {st.session_state['token']}"
    }

def add_budget(month, category, amount, is_recurring=False):
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

def get_month_options(existing_months):
    """
    Returns:
    - All months from Jan of current year → current month
    - Next month
    - Keeps existing months (safe if DB has data)
    """
    today = pd.Timestamp.today()
    current_period = today.to_period("M")

    # All months from Jan → current month (same year)
    year_start = pd.Period(f"{today.year}-01", freq="M")
    months = {
        str(year_start + i)
        for i in range(current_period.month)
    }

    # Add next month
    months.add(str(current_period + 1))

    # Merge with DB months (defensive, future-proof)
    months |= set(existing_months)

    return sorted(months)

def get_default_month_index(months):
    current_month = str(pd.Timestamp.today().to_period("M"))
    return months.index(current_month) if current_month in months else 0

def get_active_month():
    """
    Returns the globally selected month.
    Falls back to current month if Dashboard hasn't set it yet.
    """
    if "active_month" in st.session_state:
        return st.session_state["active_month"]
    return str(pd.Timestamp.today().to_period("M"))

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

def get_income_api(month):
    r = requests.get(
        f"{API_URL}/income",
        params={"month": month}, headers=auth_headers()
    )
    df = pd.DataFrame(r.json())

    if not df.empty:
        df["date"] = pd.to_datetime(df["date"])

    return df

def get_expenses_api(month):
    r = requests.get(
        f"{API_URL}/expenses",
        params={"month": month}, headers=auth_headers()
    )
    df = pd.DataFrame(r.json())

    if not df.empty:
        df["date"] = pd.to_datetime(df["date"])

    return df

def create_income_api(payload: dict):
    r = requests.post(f"{API_URL}/income", json=payload, headers=auth_headers())
    r.raise_for_status()
    return r.json()


def create_expense_api(payload: dict):
    r = requests.post(f"{API_URL}/expenses", json=payload, headers=auth_headers())
    r.raise_for_status()
    return r.json()

def get_dashboard_summary_api(month):
    r = requests.get(
        f"{API_URL}/dashboard-summary",
        params={"month": month}, headers=auth_headers()
    )
    return r.json()

def apply_income_filters(df):
    if df.empty:
        return df

    col1, col2 = st.columns(2)

    source = col1.text_input("Search Source")
    category = col2.multiselect(
        "Category",
        options=sorted(df["category"].dropna().unique())
    )

    if source:
        df = df[df["source"].str.contains(source, case=False, na=False)]

    if category:
        df = df[df["category"].isin(category)]

    return df
# ==============================
# GLOBAL ACTIVE MONTH INIT
# ==============================
if "active_month" not in st.session_state:
    st.session_state["active_month"] = str(
        pd.Timestamp.today().to_period("M")
    )

# ==============================
# INCOME TAB (ADDED TABLE)
# ==============================
if menu == "Income":
    st.subheader("Add Income")
    with st.form("income_form", clear_on_submit=True):
        d = st.date_input("Date", value=date.today(), key="income_date")
        source = st.text_input("Income Source", key="income_source")
        category = st.selectbox("Category", INCOME_CATEGORIES, key="income_category")
        amount = st.number_input("Amount", min_value=0.0, key="income_amount")

        income_type = st.selectbox(
            "Income Type",
            ["One-time", "Recurring"],
            key="income_type"
        )

        if st.form_submit_button("Add Income"):
            create_income_api({
                "date": str(d),
                "source": source,
                "category": category,
                "amount": amount,
                "income_type": income_type
            })



            st.rerun()

    st.divider()
    active_month = get_active_month()

    df = get_income_api(active_month)
    with st.expander("🔎 Filters", expanded=False):
        df = apply_income_filters(df)

    # keep id separately for DB actions
    ids = df["id"]

    # drop UI-hidden columns
    df = df.drop(columns=["id", "income_type"])

    if not df.empty:
        df["Delete"] = False
        edited = st.data_editor(
            df,
            key="income_editor",
            use_container_width=True,
            hide_index=True,  # ✅ removes index column
            column_config={
                "date": st.column_config.DateColumn(
                    "Date",
                    format="YYYY-MM-DD"
                ),
                "source": st.column_config.TextColumn("Source"),
                "category": st.column_config.SelectboxColumn(
                    "Category",
                    options=INCOME_CATEGORIES
                ),
                "amount": st.column_config.NumberColumn(
                    "Amount",
                    format="%.2f"
                ),

                # 🔒 internal / hidden
                "income_type": st.column_config.TextColumn(disabled=True),
                "id": st.column_config.TextColumn(disabled=True),
                "Month": st.column_config.TextColumn(disabled=True),
                "Delete": st.column_config.CheckboxColumn("Delete")
            }
        )
        edited["id"] = ids.values

        if st.button("Save Income Changes", key="save_income"):
            for _, r in edited.iterrows():
                requests.put(
                    f"{API_URL}/income/{r['id']}",
                    json={
                        "date": str(r["date"]),
                        "source": r["source"],
                        "category": r["category"],
                        "amount": r["amount"],
                        "income_type": "One-time"
                    }, headers=auth_headers()
                )
            st.rerun()

        if st.button("Delete Selected Income", key="delete_income"):
            for id in edited.loc[edited["Delete"], "id"]:
                requests.delete(f"{API_URL}/income/{id}", headers=auth_headers())
            st.rerun()

# ==============================
# EXPENSE TAB (VARIABLE + TABLE)
# ==============================
if menu == "Expenses":
    st.subheader("Add Variable Expense")
    with st.form("expense_form", clear_on_submit=True):
        d = st.date_input("Date", value=date.today(), key="expense_date")
        name = st.text_input("Expense Name", key="expense_name")
        category = st.selectbox("Category", EXPENSE_CATEGORIES, key="expense_category")
        payment = st.selectbox("Payment Method", PAYMENT_METHODS, key="expense_payment")
        amount = st.number_input("Amount", min_value=0.0, key="expense_amount")

        if st.form_submit_button("Add Expense"):
            create_expense_api({
                "date": str(d),
                "name": name,
                "category": category,
                "amount": amount,
                "payment_method": payment,
                "expense_type": "Variable"
            })

            st.rerun()

    st.divider()
    active_month = get_active_month()
    df = get_expenses_api(active_month)
    df = df[df["expense_type"] == "Variable"]

    with st.expander("🔎 Filters", expanded=False):
        df = apply_expense_filters(df)

    ids = df["id"]
    df = df.drop(columns=["id", "expense_type"])

    if not df.empty:
        df["Delete"] = False
        edited = st.data_editor(
            df,
            key="expense_editor",
            use_container_width=True,
            hide_index=True,  # ✅ removes index column
            column_config={
                "date": st.column_config.DateColumn("Date", format="YYYY-MM-DD"),
                "name": st.column_config.TextColumn("Name"),
                "category": st.column_config.SelectboxColumn(
                    "Category", options=EXPENSE_CATEGORIES
                ),
                "payment_method": st.column_config.SelectboxColumn(
                    "Payment Method", options=PAYMENT_METHODS
                ),
                "amount": st.column_config.NumberColumn(
                    "Amount", format="%.2f"
                ),

                # hidden/internal
                "expense_type": st.column_config.TextColumn(disabled=True),
                "Month": st.column_config.TextColumn(disabled=True),
                "id": st.column_config.TextColumn(disabled=True),
                "Delete": st.column_config.CheckboxColumn("Delete")
            }
        )
        edited["id"] = ids.values

        if st.button("Save Expense Changes", key="save_expense"):
            for _, r in edited.iterrows():
                requests.put(
                    f"{API_URL}/expenses/{r['id']}",
                    json={
                        "date": str(r["date"]),
                        "name": r["name"],
                        "category": r["category"],
                        "amount": r["amount"],
                        "payment_method": r["payment_method"],
                        "expense_type": "Variable"
                    }, headers=auth_headers()
                )
            st.rerun()

        if st.button("Delete Selected Expenses", key="delete_expense"):
            for id in edited.loc[edited["Delete"], "id"]:
                requests.delete(f"{API_URL}/expenses/{id}", headers=auth_headers())
            st.rerun()

# ==============================
# RECURRING TAB (UNCHANGED + TABLE)
# ==============================
if menu == "Recurring":
    st.subheader("Add Recurring Expense")
    with st.form("recurring_form", clear_on_submit=True):
        d = st.date_input("Start Date", value=date.today(), key="recurring_date")
        name = st.text_input("Name", key="recurring_name")
        category = st.selectbox("Category", RECURRING_CATEGORIES, key="recurring_category")
        payment = st.selectbox("Payment Method", PAYMENT_METHODS, key="recurring_payment")
        amount = st.number_input("Amount", min_value=0.0, key="recurring_amount")

        if st.form_submit_button("Save Recurring"):
            create_expense_api({
                "date": str(d),
                "name": name,
                "category": category,
                "amount": amount,
                "payment_method": payment,
                "expense_type": "Recurring"
            })

            st.rerun()

    st.divider()
    active_month = get_active_month()
    df = get_expenses_api(active_month)
    df = df[df["expense_type"] == "Recurring"]
    with st.expander("🔎 Filters", expanded=False):
        df = apply_recurring_filters(df)

    ids = df["id"]
    df = df.drop(columns=["id", "expense_type"])
    if not df.empty:
        df["Delete"] = False
        edited = st.data_editor(
            df,
            key="recurring_editor",
            use_container_width=True,
            hide_index=True,  # ✅ ADD THIS
            column_config={
                "date": st.column_config.DateColumn("Date", format="YYYY-MM-DD"),
                "name": st.column_config.TextColumn("Name"),
                "category": st.column_config.SelectboxColumn(
                    "Category", options=RECURRING_CATEGORIES
                ),
                "payment_method": st.column_config.SelectboxColumn(
                    "Payment Method", options=PAYMENT_METHODS
                ),
                "amount": st.column_config.NumberColumn(
                    "Amount", format="%.2f"
                ),

                # hidden/internal
                "expense_type": st.column_config.TextColumn(disabled=True),
                "Month": st.column_config.TextColumn(disabled=True),
                "id": st.column_config.TextColumn(disabled=True),
                "Delete": st.column_config.CheckboxColumn("Delete")
            }
        )
        edited["id"] = ids.values

        if st.button("Save Recurring Changes", key="save_recurring"):
            for _, r in edited.iterrows():
                requests.put(
                    f"{API_URL}/expenses/{r['id']}",
                    json={
                        "date": str(r["date"]),
                        "name": r["name"],
                        "category": r["category"],
                        "amount": r["amount"],
                        "payment_method": r["payment_method"],
                        "expense_type": "Recurring"
                    }, headers=auth_headers()
                )
            st.rerun()

        if st.button("Delete Selected Recurring", key="delete_recurring"):
            for id in edited.loc[edited["Delete"], "id"]:
                requests.delete(f"{API_URL}/expenses/{id}", headers=auth_headers())
            st.rerun()

# ==============================
# DASHBOARD
# ==============================
if menu == "Dashboard":
    income_df = get_income_api(get_active_month())
    expense_df = get_expenses_api(get_active_month())

    # ----- Month selection (ALWAYS visible) -----
    existing_months = set(income_df.get("Month", [])).union(
        set(expense_df.get("Month", []))
    )

    months = get_month_options(existing_months)
    default_index = get_default_month_index(months)

    month = st.selectbox(
        "Month",
        months,
        index=default_index,
        key="dashboard_month"
    )

    # Single source of truth
    st.session_state["active_month"] = month

    # ----- Auto-carry budgets -----
    added_budgets = auto_apply_recurring_budgets(month)
    if added_budgets:
        st.info(
            f"📋 Budgets carried over from last month: "
            + ", ".join(added_budgets)
        )

    # ----- Auto-apply recurring income / expenses -----
    added_inc = auto_apply_recurring_income(income_df, month)
    added_exp = auto_apply_recurring_expenses(expense_df, month)

    if added_inc:
        income_df = get_all_income()
    if added_exp:
        expense_df = get_all_expenses()

    # ----- If still no data, stop after selector -----
    if income_df.empty and expense_df.empty:
        st.info("No data yet. Start by adding income, expenses, or budgets.")

    # ==============================
    # KPIs
    # ==============================
    summary = get_dashboard_summary_api(month)

    income_total = summary["income_total"]
    expense_total = summary["expense_total"]
    balance = summary["balance"]

    c1, c2, c3 = st.columns(3)
    c1.metric("Income", f"€{income_total:,.2f}")
    c2.metric("Expenses", f"€{expense_total:,.2f}")
    c3.metric(
        "Balance",
        f"€{balance:,.2f}",
        delta_color="inverse" if balance < 0 else "normal"
    )

    st.divider()

    # ==============================
    # PREP DATA
    # ==============================
    budgets = load_df("SELECT category, budget FROM budgets WHERE month=%s", (month,))
    actual = (
        expense_df[expense_df["Month"] == month]
        .groupby("category")["amount"]
        .sum()
        .reset_index()
    )

    if not budgets.empty:
        comparison = budgets.merge(actual, on="category", how="left").fillna(0)
        comparison["overspend"] = comparison["amount"] - comparison["budget"]

    # ==============================
    # ROW 1: Actual vs Budget | Expense Composition
    # ==============================
    col1, col2 = st.columns(2)

    # ----- Actual vs Budget -----
    with col1:
        if not budgets.empty:
            fig, ax = plt.subplots(figsize=(4, 3))
            fig.patch.set_facecolor(COLORS["bg"])
            ax.set_facecolor(COLORS["bg"])

            x = range(len(comparison))
            actual_colors = [
                COLORS["actual_bad"] if a > b else COLORS["actual_ok"]
                for a, b in zip(comparison["amount"], comparison["budget"])
            ]

            ax.bar(x, comparison["budget"], width=0.4,
                   color=COLORS["budget"], label="Budget")
            ax.bar([i + 0.4 for i in x], comparison["amount"], width=0.4,
                   color=actual_colors, label="Actual")

            ax.set_xticks([i + 0.2 for i in x])
            ax.set_xticklabels(comparison["category"], rotation=30, ha="right", fontsize=8)
            ax.set_title("Actual vs Budget", fontsize=10, color="white")
            ax.tick_params(colors="white", labelsize=8)
            ax.grid(axis="y", color=COLORS["grid"], alpha=0.4)
            ax.legend(fontsize=8)

            st.pyplot(fig, use_container_width=False)
        else:
            st.info("No budgets set.")

    # ----- Expense Composition -----
    with col2:
        category_spend = (
            expense_df[expense_df["Month"] == month]
            .groupby("category")["amount"]
            .sum()
        )

        if not category_spend.empty:
            fig, ax = plt.subplots(figsize=(4, 3))
            fig.patch.set_facecolor(COLORS["bg"])
            ax.set_facecolor(COLORS["bg"])

            ax.pie(
                category_spend,
                startangle=90,
                autopct="%1.0f%%",
                wedgeprops={"width": 0.4},
                textprops={"fontsize": 8, "color": "white"}
            )

            ax.set_title("Expense Composition", fontsize=10, color="white")

            ax.legend(
                category_spend.index,
                loc="center left",
                bbox_to_anchor=(1.0, 0.5),
                fontsize=8
            )

            st.pyplot(fig, use_container_width=False)
        else:
            st.info("No expenses.")

    st.divider()

    # ==============================
    # ROW 2: Overspend Ranking | Monthly Cashflow
    # ==============================
    col3, col4 = st.columns(2)

    # ----- Overspend Ranking -----
    with col3:
        if not budgets.empty:
            overspent = comparison[comparison["overspend"] > 0] \
                .sort_values("overspend", ascending=True)

            if overspent.empty:
                st.success("🎉 No categories overspent this month.")
            else:
                fig, ax = plt.subplots(figsize=(4, 3))
                fig.patch.set_facecolor(COLORS["bg"])
                ax.set_facecolor(COLORS["bg"])

                ax.barh(
                    overspent["category"],
                    overspent["overspend"],
                    color=COLORS["actual_bad"]
                )

                ax.set_title("Overspend Ranking", fontsize=10, color="white")
                ax.set_xlabel("Over Budget Amount", fontsize=9, color="white")
                ax.tick_params(colors="white", labelsize=8)
                ax.grid(axis="x", color=COLORS["grid"], alpha=0.4)

                st.pyplot(fig, use_container_width=False)

    # ----- Monthly Cashflow -----
    with col4:
        cashflow = (
            pd.DataFrame({
                "Income": income_df.groupby("Month")["amount"].sum(),
                "Expenses": expense_df.groupby("Month")["amount"].sum()
            })
            .fillna(0)
            .sort_index()
        )

        fig, ax = plt.subplots(figsize=(4, 3))
        fig.patch.set_facecolor(COLORS["bg"])
        ax.set_facecolor(COLORS["bg"])

        ax.plot(
            cashflow.index,
            cashflow["Income"],
            marker="o",
            color=COLORS["income"],
            label="Income"
        )

        ax.plot(
            cashflow.index,
            cashflow["Expenses"],
            marker="o",
            color=COLORS["expense"],
            label="Expenses"
        )

        ax.set_title("Monthly Cashflow", fontsize=10, color="white")
        ax.set_ylabel("Amount", fontsize=9, color="white")
        ax.tick_params(colors="white", labelsize=8)
        ax.grid(color=COLORS["grid"], alpha=0.4)
        ax.legend(fontsize=8)

        st.pyplot(fig, use_container_width=False)

# ==============================
# BUDGET TAB
# ==============================
if menu == "Budget":
    month = st.session_state.get("active_month")

    if not month:
        st.info("Select a month on the Dashboard to manage budgets.")
        st.stop()

    st.caption(f"📅 Budgets for {month}")

    # ------------------------------
    # Add / Update Budget Form
    # ------------------------------
    with st.form("budget_form", clear_on_submit=True):
        category = st.selectbox("Category", BUDGET_CATEGORIES, key="budget_category")
        amount = st.number_input("Budget Amount", min_value=0.0, key="budget_amount")

        is_recurring = st.checkbox(
            "🔁 Recurring budget (auto-applies every month)",
            value=True
        )

        if st.form_submit_button("Save Budget"):
            add_budget(month, category, amount, is_recurring)

            st.rerun()

    st.divider()

    # ------------------------------
    # Load budgets + actuals
    # ------------------------------
    budgets = get_budgets_for_month(month)

    expense_df = get_all_expenses()
    expense_df = expense_df[expense_df["Month"] == month]

    if budgets.empty:
        st.info("No budgets set for this month.")
        st.stop()

    actual = (
        expense_df
        .groupby("category")["amount"]
        .sum()
        .reset_index()
    )

    comparison = budgets.merge(
        actual,
        on="category",
        how="left"
    ).fillna(0)

    comparison["Variance"] = comparison["budget"] - comparison["amount"]
    comparison["Delete"] = False

    # ------------------------------
    # Editable Budget Table
    # ------------------------------
    edited = st.data_editor(
        comparison,
        use_container_width=True,
        hide_index=True,
        key="budget_editor",
        column_config={
            "month": st.column_config.TextColumn(
                "Month", disabled=True
            ),
            "category": st.column_config.TextColumn(
                "Category", disabled=True
            ),
            "budget": st.column_config.NumberColumn(
                "Budget", min_value=0.0, format="%.2f"
            ),
            "amount": st.column_config.NumberColumn(
                "Actual", disabled=True, format="%.2f"
            ),
            "Variance": st.column_config.NumberColumn(
                "Variance", disabled=True, format="%.2f"
            ),
            "is_recurring": st.column_config.CheckboxColumn(
                "Recurring"
            ),
            "Delete": st.column_config.CheckboxColumn("Delete")
        }
    )

    col1, col2 = st.columns(2)

    # ------------------------------
    # Save edits
    # ------------------------------
    with col1:
        if st.button("💾 Save Budget Changes"):
            for _, r in edited.iterrows():
                update_budget(
                    month,
                    r["category"],
                    r["budget"],
                    r["is_recurring"]
                )
            st.success("Budgets updated")
            st.rerun()

    # ------------------------------
    # Delete selected
    # ------------------------------
    with col2:
        if st.button("🗑️ Delete Selected Budgets"):
            to_delete = edited.loc[
                edited["Delete"], "category"
            ].tolist()

            if not to_delete:
                st.warning("No budgets selected for deletion.")
            else:
                delete_budgets(month, to_delete)
                st.success("Selected budgets deleted")
                st.rerun()

# ==============================
# LOG TAB (ORIGINAL BEHAVIOR PRESERVED)
# ==============================
if menu == "Log":
    st.subheader("Income Log")
    inc = get_all_income()
    if not inc.empty:
        edited = st.data_editor(inc, use_container_width=True, key="log_income")
        if st.button("Save Income Changes", key="log_save_income"):
            for _, r in edited.iterrows():
                execute(
                    "UPDATE income SET date=%s, source=%s, category=%s, amount=%s WHERE id=%s",
                    (r["date"], r["source"], r["category"], r["amount"], r["id"])
                )
            st.rerun()

    st.subheader("Expense Log")
    exp = get_all_expenses()
    if not exp.empty:
        edited = st.data_editor(exp, use_container_width=True, key="log_expense")
        if st.button("Save Expense Changes", key="log_save_expense"):
            for _, r in edited.iterrows():
                execute(
                    """UPDATE expenses
                       SET date=%s, name=%s, category=%s,
                           amount=%s, payment_method=%s, expense_type=%s
                       WHERE id=%s""",
                    (
                        r["date"], r["name"], r["category"],
                        r["amount"], r["payment_method"],
                        r["expense_type"], r["id"]
                    )
                )
            st.rerun()