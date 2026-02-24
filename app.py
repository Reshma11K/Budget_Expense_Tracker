# ==============================
# IMPORTS & APP SETUP
# ==============================
import streamlit as st
import pandas as pd
from datetime import date
from db import load_df, execute
import matplotlib.pyplot as plt

st.set_page_config(page_title="Household Budget App", layout="wide")
st.title("🏠 Household Budget App")

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
    "Rent", "Transport", "Internet", "Electricity",
    "Insurance", "Scalable Savings", "Other"
]

PAYMENT_METHODS = [
    "Cash", "Bank Transfer", "N26 V", "N26 R",
    "Edenred", "Amex", "Gebührenfrei", "Trade Republic"
]


# ==============================
# LOADERS (FIXED DATE PARSING)
# ==============================
def load_income():
    df = load_df("SELECT * FROM income ORDER BY date DESC")
    if df.empty:
        df["Month"] = []
        return df
    df["date"] = pd.to_datetime(df["date"], format="mixed")
    df["Month"] = df["date"].dt.to_period("M").astype(str)
    return df

def load_expenses():
    df = load_df("SELECT * FROM expenses ORDER BY date DESC")
    if df.empty:
        df["Month"] = []
        return df
    df["date"] = pd.to_datetime(df["date"], format="mixed")
    df["Month"] = df["date"].dt.to_period("M").astype(str)
    return df

def add_budget(month, category, amount):
    execute(
        """INSERT INTO budgets (month, category, budget)
           VALUES (%s,%s,%s)
           ON CONFLICT (month, category)
           DO UPDATE SET budget = EXCLUDED.budget""",
        (month, category, amount)
    )

def get_month_options(existing_months, future_months=6):
    """
    Returns a sorted list of YYYY-MM months including existing
    months and N future months.
    """
    today = pd.Timestamp.today().to_period("M")
    future = [str(today + i) for i in range(future_months + 1)]
    return sorted(set(existing_months).union(future))

def get_default_month_index(months):
    current_month = str(pd.Timestamp.today().to_period("M"))
    return months.index(current_month) if current_month in months else 0

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


# ==============================
# TABS (UNCHANGED)
# ==============================
tab_dashboard, tab_income, tab_expense, tab_recurring, tab_budget, tab_log = st.tabs(
    ["📊 Dashboard", "💰 Income", "🧾 Expenses", "🔁 Recurring", "📋 Budget", "📄 Log"]
)

# ==============================
# INCOME TAB (ADDED TABLE)
# ==============================
with tab_income:
    st.subheader("Add Income")
    with st.form("income_form"):
        d = st.date_input("Date", value=date.today())
        source = st.text_input("Income Source")
        category = st.selectbox("Category", INCOME_CATEGORIES)
        amount = st.number_input("Amount", min_value=0.0)
        income_type = st.selectbox(
            "Income Type",
            ["One-time", "Recurring"]
        )
        if st.form_submit_button("Add Income"):
            execute(
                "INSERT INTO income (date, source, category, amount, income_type) VALUES (%s,%s,%s,%s,%s)",
                (d, source, category, amount, income_type)
            )
            st.rerun()

    st.divider()
    df = load_income()
    if not df.empty:
        df["Delete"] = False
        edited = st.data_editor(
            df,
            key="income_editor",
            use_container_width=True,
            column_config={
                "date": st.column_config.DateColumn(
                    "Date",
                    format="YYYY-MM-DD"
                ),
                "category": st.column_config.SelectboxColumn(
                    "Category",
                    options=INCOME_CATEGORIES
                ),
                "id": st.column_config.NumberColumn(disabled=True),
                "Month": st.column_config.TextColumn(disabled=True),
                "income_type": st.column_config.SelectboxColumn(
                    "Income Type",
                    options=["One-time", "Recurring"]
                )
            }
        )

        if st.button("Save Income Changes", key="save_income"):
            for _, r in edited.iterrows():
                execute(
                    "UPDATE income SET date=%s, source=%s, category=%s, amount=%s, income_type=%s WHERE id=%s",
                    (r["date"], r["source"], r["category"], r["amount"], r["income_type"], r["id"])
                )
            st.rerun()

        if st.button("Delete Selected Income", key="delete_income"):
            execute(
                "DELETE FROM income WHERE id = ANY(%s)",
                (edited.loc[edited["Delete"], "id"].tolist(),)
            )
            st.rerun()

# ==============================
# EXPENSE TAB (VARIABLE + TABLE)
# ==============================
with tab_expense:
    st.subheader("Add Variable Expense")
    with st.form("expense_form"):
        d = st.date_input("Date", value=date.today())
        name = st.text_input("Expense Name")
        category = st.selectbox("Category", EXPENSE_CATEGORIES)
        payment = st.selectbox("Payment Method", PAYMENT_METHODS)
        amount = st.number_input("Amount", min_value=0.0)
        if st.form_submit_button("Add Expense"):
            execute(
                """INSERT INTO expenses
                   (date, name, category, amount, payment_method, expense_type)
                   VALUES (%s,%s,%s,%s,%s,'Variable')""",
                (d, name, category, amount, payment)
            )
            st.rerun()

    st.divider()
    df = load_expenses()
    df = df[df["expense_type"] == "Variable"]
    if not df.empty:
        df["Delete"] = False
        edited = st.data_editor(
            df,
            key="expense_editor",
            use_container_width=True,
            column_config={
                "date": st.column_config.DateColumn(
                    "Date",
                    format="YYYY-MM-DD"
                ),
                "category": st.column_config.SelectboxColumn(
                    "Category",
                    options=EXPENSE_CATEGORIES
                ),
                "payment_method": st.column_config.SelectboxColumn(
                    "Payment Method",
                    options=PAYMENT_METHODS
                ),
                "expense_type": st.column_config.TextColumn(
                    disabled=True
                ),
                "Month": st.column_config.TextColumn(
                    disabled=True
                ),
                "id": st.column_config.NumberColumn(
                    disabled=True
                )
            }
        )

        if st.button("Save Expense Changes", key="save_expense"):
            for _, r in edited.iterrows():
                execute(
                    """UPDATE expenses
                       SET date=%s, name=%s, category=%s, amount=%s, payment_method=%s
                       WHERE id=%s""",
                    (r["date"], r["name"], r["category"],
                     r["amount"], r["payment_method"], r["id"])
                )
            st.rerun()

        if st.button("Delete Selected Expenses", key="delete_expense"):
            execute(
                "DELETE FROM expenses WHERE id = ANY(%s)",
                (edited.loc[edited["Delete"], "id"].tolist(),)
            )
            st.rerun()

# ==============================
# RECURRING TAB (UNCHANGED + TABLE)
# ==============================
with tab_recurring:
    st.subheader("Add Recurring Expense")
    with st.form("recurring_form"):
        d = st.date_input("Start Date", value=date.today())
        name = st.text_input("Name")
        category = st.selectbox("Category", RECURRING_CATEGORIES)
        payment = st.selectbox("Payment Method", PAYMENT_METHODS)
        amount = st.number_input("Amount", min_value=0.0)
        if st.form_submit_button("Save Recurring"):
            execute(
                """INSERT INTO expenses
                   (date, name, category, amount, payment_method, expense_type)
                   VALUES (%s,%s,%s,%s,%s,'Recurring')""",
                (d, name, category, amount, payment)
            )
            st.rerun()

    st.divider()
    df = load_expenses()
    df = df[df["expense_type"] == "Recurring"]
    if not df.empty:
        df["Delete"] = False
        edited = st.data_editor(
            df,
            key="recurring_editor",
            use_container_width=True,
            column_config={
                "date": st.column_config.DateColumn("Date", format="YYYY-MM-DD"),
                "category": st.column_config.SelectboxColumn(
                    "Category",
                    options=RECURRING_CATEGORIES
                ),
                "payment_method": st.column_config.SelectboxColumn(
                    "Payment Method",
                    options=PAYMENT_METHODS
                ),
                "expense_type": st.column_config.TextColumn(disabled=True),
                "Month": st.column_config.TextColumn(disabled=True),
                "id": st.column_config.NumberColumn(disabled=True)
            }
        )

        if st.button("Save Recurring Changes", key="save_recurring"):
            for _, r in edited.iterrows():
                execute(
                    """UPDATE expenses
                       SET date=%s, name=%s, category=%s, amount=%s, payment_method=%s
                       WHERE id=%s""",
                    (r["date"], r["name"], r["category"],
                     r["amount"], r["payment_method"], r["id"])
                )
            st.rerun()

        if st.button("Delete Selected Recurring", key="delete_recurring"):
            execute(
                "DELETE FROM expenses WHERE id = ANY(%s)",
                (edited.loc[edited["Delete"], "id"].tolist(),)
            )
            st.rerun()

# ==============================
# DASHBOARD
# ==============================
with tab_dashboard:
    income_df = load_income()
    expense_df = load_expenses()

    if income_df.empty and expense_df.empty:
        st.info("No data yet.")
    else:
        # ----- Month selection -----
        existing_months = set(income_df["Month"]).union(set(expense_df["Month"]))
        months = get_month_options(existing_months, future_months=6)
        default_index = get_default_month_index(months)

        month = st.selectbox(
            "Month",
            months,
            index=default_index,
            key="dashboard_month"
        )

        # ----- Auto-apply recurring -----
        added_exp = auto_apply_recurring(expense_df, month)
        added_inc = auto_apply_recurring_income(income_df, month)

        if added_inc:
            st.info(
                f"🔁 Auto-added recurring income for {month}: "
                + ", ".join(added_inc)
            )
            income_df = load_income()

        if added_exp:
            st.info(
                f"🔁 Auto-added recurring expenses for {month}: "
                + ", ".join(added_exp)
            )
            expense_df = load_expenses()

        # ----- KPIs -----
        income_total = income_df[income_df["Month"] == month]["amount"].sum()
        expense_total = expense_df[expense_df["Month"] == month]["amount"].sum()
        balance = income_total - expense_total

        c1, c2, c3 = st.columns(3)
        c1.metric("Income", f"${income_total:,.2f}")
        c2.metric("Expenses", f"${expense_total:,.2f}")

        balance_color = "normal"
        if balance < 0:
            balance_color = "inverse"

        c3.metric(
            "Balance",
            f"${balance:,.2f}",
            delta=None,
            delta_color=balance_color
        )

        st.divider()

        # =============================
        # ROW 1: Budget Variance | Actual vs Budget
        # =============================
        col1, col2 = st.columns(2)

        # ----- Budget Variance (PRIMARY DIAGNOSTIC) -----
        with col1:
            budgets = load_df("SELECT * FROM budgets WHERE month=%s", (month,))

            if not budgets.empty:
                actual = (
                    expense_df[expense_df["Month"] == month]
                    .groupby("category")["amount"]
                    .sum()
                    .reset_index()
                )

                comparison = budgets.merge(actual, on="category", how="left").fillna(0)
                comparison["variance"] = comparison["amount"] - comparison["budget"]

                fig, ax = plt.subplots(figsize=(4, 3))

                colors = [
                    "#d62728" if v > 0 else "#2ca02c"
                    for v in comparison["variance"]
                ]

                ax.bar(
                    comparison["category"],
                    comparison["variance"],
                    color=colors
                )

                ax.axhline(0, color="black", linewidth=0.8)

                ax.set_title("Budget Variance", fontsize=10)
                ax.set_ylabel("Actual − Budget", fontsize=9)
                ax.set_xticklabels(
                    comparison["category"],
                    rotation=30,
                    ha="right",
                    fontsize=8
                )

                from matplotlib.patches import Patch
                legend_items = [
                    Patch(facecolor="#d62728", label="Overspent"),
                    Patch(facecolor="#2ca02c", label="Under Budget")
                ]
                ax.legend(handles=legend_items, fontsize=8)

                st.pyplot(fig, use_container_width=False)
            else:
                st.info("No budgets set for this month.")

        # ----- Actual vs Budget (EXPLANATORY) -----
        with col2:
            if not budgets.empty:
                fig, ax = plt.subplots(figsize=(4, 3))

                categories = comparison["category"]
                budget_vals = comparison["budget"]
                actual_vals = comparison["amount"]

                actual_colors = [
                    "#d62728" if a > b else "#2ca02c"
                    for a, b in zip(actual_vals, budget_vals)
                ]

                x = range(len(categories))

                ax.bar(
                    x,
                    budget_vals,
                    width=0.35,
                    label="Budget",
                    color="#7f7f7f"
                )

                ax.bar(
                    [i + 0.35 for i in x],
                    actual_vals,
                    width=0.35,
                    label="Actual",
                    color=actual_colors
                )

                ax.set_xticks([i + 0.175 for i in x])
                ax.set_xticklabels(categories, rotation=30, ha="right", fontsize=8)
                ax.set_title("Actual vs Budget", fontsize=10)
                ax.set_ylabel("Amount", fontsize=9)

                from matplotlib.patches import Patch
                legend_items = [
                    Patch(facecolor="#7f7f7f", label="Budget"),
                    Patch(facecolor="#2ca02c", label="Within Budget"),
                    Patch(facecolor="#d62728", label="Overspent")
                ]
                ax.legend(handles=legend_items, fontsize=8)

                st.pyplot(fig, use_container_width=False)

        st.divider()

        # =============================
        # ROW 2: Expense Composition (DESCRIPTIVE)
        # =============================
        category_spend = (
            expense_df[expense_df["Month"] == month]
            .groupby("category")["amount"]
            .sum()
        )

        if not category_spend.empty:
            fig, ax = plt.subplots(figsize=(4, 3))

            wedges, _, _ = ax.pie(
                category_spend,
                autopct="%1.0f%%",
                startangle=90,
                wedgeprops={"width": 0.35},
                textprops={"fontsize": 8}
            )

            ax.legend(
                wedges,
                category_spend.index,
                title="Category",
                loc="center left",
                bbox_to_anchor=(1.0, 0.5),
                fontsize=8
            )

            ax.set_title("Expense Composition", fontsize=10)

            st.pyplot(fig, use_container_width=False)

        st.divider()

        # =============================
        # ROW 3: Income vs Expense Trend (STRATEGIC)
        # =============================
        income_trend = (
            income_df.groupby("Month")["amount"]
            .sum()
            .sort_index()
        )

        expense_trend = (
            expense_df.groupby("Month")["amount"]
            .sum()
            .sort_index()
        )

        trend_df = pd.DataFrame({
            "Income": income_trend,
            "Expenses": expense_trend
        }).fillna(0)

        if not trend_df.empty:
            fig, ax = plt.subplots(figsize=(7, 3))

            trend_df.plot(ax=ax, marker="o")

            ax.set_title("Income vs Expenses Over Time", fontsize=10)
            ax.set_ylabel("Amount", fontsize=9)
            ax.set_xlabel("Month", fontsize=9)
            ax.legend(fontsize=8)
            plt.xticks(rotation=30, fontsize=8)
            plt.yticks(fontsize=8)

            st.pyplot(fig, use_container_width=False)

# ==============================
# BUDGET TAB (UNCHANGED – THIS FIXES YOUR ISSUE)
# ==============================
with tab_budget:
    expense_df = load_expenses()
    if not expense_df.empty:
        existing_months = set(expense_df["Month"].unique())
        months = get_month_options(existing_months, future_months=6)

        default_index = get_default_month_index(months)

        month = st.selectbox(
            "Month",
            months,
            index=default_index,
            key="budget_month"
        )

        added = auto_apply_recurring(expense_df, month)
        if added:
            st.info(
                f"🔁 Auto-added recurring expenses for {month}: "
                + ", ".join(added)
            )
            expense_df = load_expenses()

        with st.form("budget_form"):
            category = st.selectbox("Category", EXPENSE_CATEGORIES)
            amount = st.number_input("Budget Amount", min_value=0.0)
            if st.form_submit_button("Save Budget"):
                add_budget(month, category, amount)
                st.rerun()

        budgets = load_df("SELECT * FROM budgets WHERE month=%s", (month,))
        if not budgets.empty:
            actual = (
                expense_df[expense_df["Month"] == month]
                .groupby("category")["amount"]
                .sum()
                .reset_index()
            )
            comparison = budgets.merge(actual, on="category", how="left").fillna(0)
            comparison["Variance"] = comparison["budget"] - comparison["amount"]
            st.dataframe(comparison, use_container_width=True)

# ==============================
# LOG TAB (ORIGINAL BEHAVIOR PRESERVED)
# ==============================
with tab_log:
    st.subheader("Income Log")
    inc = load_income()
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
    exp = load_expenses()
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