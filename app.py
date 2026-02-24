# ==============================
# IMPORTS & APP SETUP
# ==============================
import streamlit as st
import pandas as pd
from datetime import date
import psycopg2
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
# DATABASE CONNECTION
# ==============================
def get_conn():
    return psycopg2.connect(
        host=st.secrets["DB_HOST"],
        database=st.secrets["DB_NAME"],
        user=st.secrets["DB_USER"],
        password=st.secrets["DB_PASSWORD"],
        port=int(st.secrets.get("DB_PORT", 5432)),
        sslmode="require"
    )

# ==============================
# DB HELPERS
# ==============================
def load_df(query, params=None):
    conn = get_conn()
    df = pd.read_sql(query, conn, params=params)
    conn.close()
    return df

def execute(query, params=None):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(query, params)
    conn.commit()
    conn.close()

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
        if st.form_submit_button("Add Income"):
            execute(
                "INSERT INTO income (date, source, category, amount) VALUES (%s,%s,%s,%s)",
                (d, source, category, amount)
            )
            st.rerun()

    st.divider()
    df = load_income()
    if not df.empty:
        df["Delete"] = False
        edited = st.data_editor(df, key="income_editor", use_container_width=True)

        if st.button("Save Income Changes", key="save_income"):
            for _, r in edited.iterrows():
                execute(
                    "UPDATE income SET date=%s, source=%s, category=%s, amount=%s WHERE id=%s",
                    (r["date"], r["source"], r["category"], r["amount"], r["id"])
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
        edited = st.data_editor(df, key="expense_editor", use_container_width=True)

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
        edited = st.data_editor(df, key="recurring_editor", use_container_width=True)

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
# DASHBOARD (UNCHANGED LOGIC)
# ==============================
with tab_dashboard:
    income_df = load_income()
    expense_df = load_expenses()

    if income_df.empty and expense_df.empty:
        st.info("No data yet.")
    else:
        months = sorted(set(income_df["Month"]).union(set(expense_df["Month"])))
        month = st.selectbox("Month", months, key="dashboard_month")

        income_total = income_df[income_df["Month"] == month]["amount"].sum()
        expense_total = expense_df[expense_df["Month"] == month]["amount"].sum()

        c1, c2, c3 = st.columns(3)
        c1.metric("Income", f"${income_total:,.2f}")
        c2.metric("Expenses", f"${expense_total:,.2f}")
        c3.metric("Balance", f"${income_total - expense_total:,.2f}")

        expense_plot = (
            expense_df[expense_df["Month"] == month]
            .groupby("category")["amount"]
            .sum()
        )

        if not expense_plot.empty:
            fig, ax = plt.subplots()
            expense_plot.plot(kind="bar", ax=ax)
            ax.set_title("Expenses by Category")
            st.pyplot(fig)

# ==============================
# BUDGET TAB (UNCHANGED – THIS FIXES YOUR ISSUE)
# ==============================
with tab_budget:
    expense_df = load_expenses()
    if not expense_df.empty:
        months = sorted(expense_df["Month"].unique())
        month = st.selectbox("Month", months, key="budget_month")

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