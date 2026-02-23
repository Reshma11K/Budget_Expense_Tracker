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
st.write("Track income, expenses, budgets, recurring items and forecast your financial future.")

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
def add_transaction(d, t_type, name, category, amount):
    execute(
        """
        INSERT INTO transactions (date, type, name, category, amount)
        VALUES (%s,%s,%s,%s,%s)
        """,
        (d, t_type, name, category, amount)
    )

def load_transactions():
    df = load_table("SELECT * FROM transactions")
    if df.empty:
        return df
    df["date"] = pd.to_datetime(df["date"])
    df["Month"] = df["date"].dt.to_period("M").astype(str)
    return df

# ==============================
# RECURRING RULES
# ==============================
def add_recurring(name, t_type, category, amount, active):
    execute(
        """
        INSERT INTO recurring_rules (name, type, category, amount, active)
        VALUES (%s,%s,%s,%s,%s)
        """,
        (name, t_type, category, amount, active)
    )

# ==============================
# INPUT FORMS
# ==============================
st.header("💰 Add Income")

with st.form("income_form"):
    source = st.text_input("Income Source")
    category = st.text_input("Category")
    amount = st.number_input("Amount", min_value=0.0)
    submit = st.form_submit_button("Add Income")

    if submit:
        add_transaction(date.today(), "Income", source, category, amount)
        st.success("Income added")
        st.rerun()

st.header("🧾 Add Expense")

with st.form("expense_form"):
    name = st.text_input("Expense Name")
    category = st.text_input("Category")
    amount = st.number_input("Amount", min_value=0.0)
    submit = st.form_submit_button("Add Expense")

    if submit:
        add_transaction(date.today(), "Expense", name, category, amount)
        st.success("Expense added")
        st.rerun()

# ==============================
# RECURRING RULES
# ==============================
st.header("🔁 Recurring Monthly Templates")

with st.form("recurring_form"):
    r_name = st.text_input("Name")
    r_type = st.selectbox("Type", ["Income", "Expense"])
    r_category = st.text_input("Category")
    r_amount = st.number_input("Amount", min_value=0.0)
    r_active = st.checkbox("Active", True)

    if st.form_submit_button("Save Recurring Rule"):
        add_recurring(r_name, r_type, r_category, r_amount, r_active)
        st.success("Recurring rule saved")
        st.rerun()

rules_df = load_table("SELECT * FROM recurring_rules")

if not rules_df.empty:
    st.subheader("✏️ Manage Recurring Rules")
    edited = st.data_editor(rules_df, use_container_width=True)

    if st.button("💾 Save Rule Changes"):
        for _, r in edited.iterrows():
            execute(
                """
                UPDATE recurring_rules
                SET name=%s, type=%s, category=%s, amount=%s, active=%s
                WHERE id=%s
                """,
                (r["name"], r["type"], r["category"], r["amount"], r["active"], r["id"])
            )
        st.success("Rules updated")
        st.rerun()

# ==============================
# DASHBOARD
# ==============================
st.header("📊 Dashboard")

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
    c3.metric("Balance", f"${income - expenses:,.2f}")

    if not month_tx.empty:
        fig, ax = plt.subplots()
        month_tx[month_tx["type"] == "Expense"] \
            .groupby("category")["amount"].sum().plot(kind="bar", ax=ax)
        st.pyplot(fig)

# ==============================
# TRANSACTION LOG
# ==============================
st.header("📄 Transaction Log")

if not tx.empty:
    editor_df = tx.sort_values("date", ascending=False)[
        ["id", "date", "type", "name", "category", "amount"]
    ]

    edited = st.data_editor(editor_df, use_container_width=True)

    if st.button("💾 Save Transaction Changes"):
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