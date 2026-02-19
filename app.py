import streamlit as st
import pandas as pd
from datetime import date
import psycopg2
import matplotlib.pyplot as plt
import seaborn as sns
from dotenv import load_dotenv

# ==============================
# APP CONFIG
# ==============================
st.set_page_config(page_title="Household Budget", layout="wide")
st.title("🏠 Household Budget")
st.caption("Personal finance command center")

# ==============================
# CONSTANTS
# ==============================
VARIABLE_EXPENSE_CATEGORIES = [
    "Grocery/Utilities", "Foodgasm", "Wants/Need", "Entertainment",
    "Emergency", "Invest", "Savings", "Travel", "Gifts", "Others"
]

RECURRING_EXPENSE_CATEGORIES = [
    "Rent", "Mobile bills", "Internet", "Electricity",
    "Scalable Savings", "Transportation Voo", "Transportation Ruu"
]

INCOME_CATEGORIES = ["Salary", "Bonus", "Tax Returns", "Edenred", "Other"]

PAYMENT_METHODS = [
    "Amex", "Gebührenfrei", "Trade Republic", "N26-R",
    "N26-V", "Bank Transfer", "Edenred", "Cash"
]

# ==============================
# DATABASE (SUPABASE POSTGRES)
# ==============================
def get_conn():
    print(f"Testing if we get values {st.secrets["DB_PASSWORD"]}")
    return psycopg2.connect(
        host="db.wleacljuyyihiqqnrtls.supabase.co",
        database="postgres",
        user="postgres",
        password="Budget_Expense_Tracker",
        port=5432
    )

def init_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        id SERIAL PRIMARY KEY,
        date DATE,
        type TEXT,
        name TEXT,
        category TEXT,
        amount NUMERIC,
        expense_type TEXT,
        payment_method TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS budgets (
        id SERIAL PRIMARY KEY,
        month TEXT,
        category TEXT,
        budget NUMERIC
    )
    """)

    conn.commit()
    conn.close()

init_db()

# ==============================
# HELPERS
# ==============================
def load_table(table):
    conn = get_conn()
    df = pd.read_sql(f"SELECT * FROM {table}", conn)
    conn.close()
    return df

def delete_row(row_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM transactions WHERE id = %s", (row_id,))
    conn.commit()
    conn.close()

def add_transaction(d, t, name, cat, amt, et="", pm=""):
    if t == "Income":
        et, pm = "", ""

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO transactions
        (date, type, name, category, amount, expense_type, payment_method)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (d, t, name, cat, amt, et, pm))
    conn.commit()
    conn.close()

def load_transactions():
    df = load_table("transactions")
    if df.empty:
        return df
    df["Date"] = pd.to_datetime(df["date"])
    df["Month"] = df["Date"].dt.to_period("M").astype(str)
    return df

# ==============================
# LOAD DATA
# ==============================
transactions = load_transactions()
months = sorted(transactions["Month"].unique()) if not transactions.empty else []

# ==============================
# NAVIGATION
# ==============================
tab_dashboard, tab_income, tab_expenses, tab_budget, tab_settings = st.tabs(
    ["Dashboard", "Income", "Expenses", "Budget", "Settings"]
)

# ==============================
# DASHBOARD
# ==============================
with tab_dashboard:
    if transactions.empty:
        st.info("No data yet.")
    else:
        m = st.selectbox("Month", months, key="dash_month")
        tx = transactions[transactions["Month"] == m]

        inc = tx[tx["type"] == "Income"]["amount"].sum()
        exp = tx[tx["type"] == "Expense"]["amount"].sum()

        c1, c2, c3 = st.columns(3)
        c1.metric("Income", f"${inc:,.2f}")
        c2.metric("Expenses", f"${exp:,.2f}")
        c3.metric("Balance", f"${inc-exp:,.2f}")

# ==============================
# SETTINGS
# ==============================
with tab_settings:
    st.write("Storage: Supabase PostgreSQL ✅")