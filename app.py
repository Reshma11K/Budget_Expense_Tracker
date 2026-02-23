# ==============================
# IMPORTS & APP SETUP
# ==============================
import streamlit as st
import pandas as pd
from datetime import datetime, date
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
    "Foodgasm", "Wants/Need", "Entertainment", "Emergency", "Invest",
    "Savings", "Travel", "Gifts", "Others"
]

RECURRING_CATEGORIES = [
    "Rent", "Transport",
    "Internet", "Electricity", "Scalable Savings", "Insurance", "Other"
]

PAYMENT_METHODS = [
    "Cash", "Bank Transfer", "N26 V", "N26 R", "Edenred", "Amex", "Gebührenfrei", "Trade Republic"
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
def load_table(query, params=None):
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
# TRANSACTIONS
# ==============================
def add_transaction(d, t_type, name, category, amount, payment_method=None):
    execute(
        """
        INSERT INTO transactions (date, type, name, category, amount, payment_method)
        VALUES (%s,%s,%s,%s,%s,%s)
        """,
        (d, t_type, name, category, amount, payment_method)
    )

def load_transactions():
    df = load_table("SELECT * FROM transactions ORDER BY date DESC")
    if df.empty:
        return df
    df["date"] = pd.to_datetime(df["date"])
    df["Month"] = df["date"].dt.to_period("M").astype(str)
    return df

# ==============================
# RECURRING RULES
# ==============================
def add_recurring(d, t_type, name, category, amount, payment_method=None):
    execute(
        """
        INSERT INTO recurring_rules (date, type, name, category, amount, payment_method)
        VALUES (%s,%s,%s,%s,%s,%s)
        """,
        (d, t_type, name, category, amount, payment_method)
    )

# ==============================
# BUDGET
# ==============================
def add_budget(month, category, amount):
    execute(
        """
        INSERT INTO budgets (month, category, budget)
        VALUES (%s,%s,%s)
        """,
        (month, category, amount)
    )

# ==============================
# TABS
# ==============================
tab_dashboard, tab_income, tab_expense, tab_recurring, tab_budget, tab_forecast, tab_log = st.tabs(
    ["📊 Dashboard", "💰 Income", "🧾 Expenses", "🔁 Recurring", "📋 Budget", "🔮 Forecast", "📄 Log"]
)

# ==============================
# INCOME TAB
# ==============================
with tab_income:
    st.subheader("Add Income")

    with st.form("income_form"):
        source = st.text_input("Income Source")
        category = st.selectbox("Category", INCOME_CATEGORIES)
        amount = st.number_input("Amount", min_value=0.0)
        if st.form_submit_button("Add Income"):
            add_transaction(date.today(), "Income", source, category, amount)
            st.success("Income added")
            st.rerun()

# ==============================
# EXPENSE TAB
# ==============================
with tab_expense:
    st.subheader("Add Expense")

    with st.form("expense_form"):
        name = st.text_input("Expense Name")
        category = st.selectbox("Category", EXPENSE_CATEGORIES)
        payment = st.selectbox("Payment Method", PAYMENT_METHODS)
        amount = st.number_input("Amount", min_value=0.0)
        if st.form_submit_button("Add Expense"):
            add_transaction(date.today(), "Expense", name, category, amount, payment)
            st.success("Expense added")
            st.rerun()

# ==============================
# RECURRING TAB
# ==============================
with tab_recurring:
    st.subheader("Recurring Rules")

    with st.form("recurring_form"):
        name = st.text_input("Name")
        category = st.selectbox("Category", RECURRING_CATEGORIES)
        payment = st.selectbox("Payment Method", PAYMENT_METHODS)
        amount = st.number_input("Amount", min_value=0.0)
        active = st.checkbox("Active", True)

        if st.form_submit_button("Save Rule"):
            add_recurring(date.today(), "Recurring", name, category, amount, payment)
            st.success("Recurring rule saved")
            st.rerun()


# ==============================
# DASHBOARD TAB
# ==============================
with tab_dashboard:
    tx = load_transactions()

    if not tx.empty:
        months = sorted(tx["Month"].unique())
        selected_month = st.selectbox("Select Month", months)

        month_tx = tx[tx["Month"] == selected_month]
        income = month_tx[month_tx["type"] == "Income"]["amount"].sum()
        expenses = month_tx[month_tx["type"] == "Expense"]["amount"].sum()

        c1, c2, c3 = st.columns(3)
        c1.metric("Income", f"${income:,.2f}")
        c2.metric("Expenses", f"${expenses:,.2f}")
        c3.metric("Balance", f"${income-expenses:,.2f}")

        if not month_tx.empty:
            expense_data = (
                month_tx[month_tx["type"] == "Expense"]
                .groupby("category")["amount"]
                .sum()
            )

            if not expense_data.empty:
                fig, ax = plt.subplots()
                expense_data.plot(kind="bar", ax=ax)
                ax.set_title("Expenses by Category")
                st.pyplot(fig)
            else:
                st.info("No expenses recorded for this month yet.")

# ==============================
# BUDGET TAB
# ==============================
with tab_budget:
    tx = load_transactions()
    if not tx.empty:
        months = sorted(tx["Month"].unique())
        month = st.selectbox("Month", months)

        with st.form("budget_form"):
            category = st.selectbox("Category", EXPENSE_CATEGORIES)
            amount = st.number_input("Budget Amount", min_value=0.0)
            if st.form_submit_button("Save Budget"):
                add_budget(month, category, amount)
                st.success("Budget saved")
                st.rerun()

        budgets = load_table("SELECT * FROM budgets WHERE month=%s", (month,))
        if not budgets.empty:
            expense_tx = tx[(tx["Month"] == month) & (tx["type"] == "Expense")]
            actual = expense_tx.groupby("category")["amount"].sum().reset_index()

            comparison = pd.merge(
                budgets, actual,
                left_on="category",
                right_on="category",
                how="left"
            ).fillna(0)

            comparison["Variance"] = comparison["budget"] - comparison["amount"]

            st.dataframe(comparison, use_container_width=True)
            st.bar_chart(comparison.set_index("category")[["budget", "amount"]])

# ==============================
# FORECAST TAB
# ==============================
with tab_forecast:
    tx = load_transactions()
    rules = load_table("SELECT * FROM recurring_rules")

    if not tx.empty and not rules.empty:
        months_ahead = st.slider("Forecast Months", 1, 12, 6)
        last_month = pd.Period(max(tx["Month"]), freq="M")

        forecast_rows = []

        for i in range(1, months_ahead + 1):
            future_month = str(last_month + i)
            for _, r in rules.iterrows():
                forecast_rows.append({
                    "Month": future_month,
                    "Type": r["type"],
                    "Category": r["category"],
                    "Amount": r["amount"]
                })

        forecast_df = pd.DataFrame(forecast_rows)
        st.dataframe(forecast_df)

# ==============================
# LOG TAB
# ==============================
with tab_log:
    tx = load_transactions()
    if not tx.empty:
        edited = st.data_editor(tx, use_container_width=True)

        if st.button("Save Transaction Changes"):
            for _, r in edited.iterrows():
                execute(
                    """
                    UPDATE transactions
                    SET date=%s, type=%s, name=%s, category=%s, amount=%s
                    WHERE id=%s
                    """,
                    (r["date"], r["type"], r["name"], r["category"], r["amount"], r["id"])
                )
            st.success("Transactions updated")
            st.rerun()