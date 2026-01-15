# ==============================
# IMPORTS & APP SETUP
# ==============================
import streamlit as st
import pandas as pd
from datetime import datetime
import os
import matplotlib.pyplot as plt

st.set_page_config(page_title="Household Budget App", layout="wide")

st.title("🏠 Household Budget App")
st.write("Track income, expenses, budgets, recurring items and forecast your financial future.")

# ==============================
# FILE & DATA HELPERS
# ==============================

def get_monthly_filename():
    now = datetime.now()
    return f"budget_{now.year}_{now.month:02d}.xlsx"

def load_data(sheet_name):
    filename = get_monthly_filename()

    if not os.path.exists(filename):
        return pd.DataFrame()

    try:
        return pd.read_excel(filename, sheet_name=sheet_name)
    except ValueError:
        return pd.DataFrame()

def save_data(df, sheet_name):
    filename = get_monthly_filename()

    if os.path.exists(filename):
        with pd.ExcelWriter(filename, mode="a", engine="openpyxl", if_sheet_exists="replace") as writer:
            df.to_excel(writer, sheet_name=sheet_name, index=False)
    else:
        with pd.ExcelWriter(filename, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name=sheet_name, index=False)

# ==============================
# TRANSACTION ENGINE
# ==============================

def add_transaction(date, t_type, name, category, amount):
    df = load_data("Transactions")

    new_row = pd.DataFrame(
        [[date, t_type, name, category, amount]],
        columns=["Date", "Type", "Name", "Category", "Amount"]
    )

    df = pd.concat([df, new_row], ignore_index=True)
    save_data(df, "Transactions")

def load_transactions_with_month():
    df = load_data("Transactions")

    if df.empty:
        return df

    if "Date" not in df.columns:
        df["Date"] = pd.Timestamp.today()

    df["Date"] = pd.to_datetime(df["Date"])
    df["Month"] = df["Date"].dt.to_period("M").astype(str)

    return df

# ==============================
# RECURRING ENGINE HELPERS
# ==============================

def get_existing_recurring_keys(transactions_df, target_month):
    month_tx = transactions_df[transactions_df["Month"] == target_month]

    keys = set()
    for _, row in month_tx.iterrows():
        keys.add((row["Month"], row["Name"], row["Type"]))

    return keys

# ==============================
# FORECAST ENGINE
# ==============================

def generate_forecast(transactions_df, rules_df, months_ahead=6):
    if transactions_df.empty or rules_df.empty:
        return pd.DataFrame()

    last_month = pd.Period(max(transactions_df["Month"]), freq="M")
    future_rows = []

    for i in range(1, months_ahead + 1):
        future_month = str(last_month + i)

        for _, rule in rules_df.iterrows():
            if rule["Active"]:
                future_rows.append({
                    "Month": future_month,
                    "Type": rule["Type"],
                    "Name": rule["Name"],
                    "Category": rule["Category"],
                    "Amount": rule["Amount"]
                })

    return pd.DataFrame(future_rows)

# ==============================
# INPUT FORMS
# ==============================

st.header("💰 Add Income")

with st.form("income_form"):
    source = st.text_input("Income Source")
    category = st.text_input("Category (Job, Side Hustle)")
    amount = st.number_input("Amount", min_value=0.0)
    submit_income = st.form_submit_button("Add Income")

    if submit_income:
        add_transaction(datetime.today(), "Income", source, category, amount)
        st.success("Income added!")

st.header("🧾 Add Expense")

with st.form("expense_form"):
    name = st.text_input("Expense Name")
    category = st.text_input("Category (Groceries, Rent, Utilities)")
    amount = st.number_input("Amount", min_value=0.0)
    submit_expense = st.form_submit_button("Add Expense")

    if submit_expense:
        add_transaction(datetime.today(), "Expense", name, category, amount)
        st.success("Expense added!")

# ==============================
# RECURRING RULES
# ==============================

st.header("🔁 Recurring Monthly Templates")

with st.form("recurring_form"):
    r_name = st.text_input("Name")
    r_type = st.selectbox("Type", ["Income", "Expense"])
    r_category = st.text_input("Category")
    r_amount = st.number_input("Amount", min_value=0.0)
    r_active = st.checkbox("Active", value=True)

    submit_recurring = st.form_submit_button("Save Recurring Rule")

    if submit_recurring:
        df = load_data("RecurringRules")
        new_row = pd.DataFrame([[r_name, r_type, r_category, r_amount, r_active]],
                               columns=["Name", "Type", "Category", "Amount", "Active"])
        df = pd.concat([df, new_row], ignore_index=True)
        save_data(df, "RecurringRules")
        st.success("Recurring rule saved!")

st.subheader("✏️ Manage Recurring Rules")

rules_df = load_data("RecurringRules")

if not rules_df.empty:
    edited_rules = st.data_editor(rules_df, num_rows="dynamic", use_container_width=True)
    if st.button("💾 Save Rule Changes"):
        save_data(edited_rules, "RecurringRules")
        st.success("Rules updated!")

# ==============================
# DASHBOARD
# ==============================

st.header("📊 Dashboard")

transactions = load_transactions_with_month()

if not transactions.empty:
    months = sorted(transactions["Month"].unique())
    selected_month = st.selectbox("Select Month", months)

    month_tx = transactions[transactions["Month"] == selected_month]
    income_tx = month_tx[month_tx["Type"] == "Income"]
    expense_tx = month_tx[month_tx["Type"] == "Expense"]

    total_income = income_tx["Amount"].sum()
    total_expenses = expense_tx["Amount"].sum()
    balance = total_income - total_expenses

    col1, col2, col3 = st.columns(3)
    col1.metric("Income", f"${total_income:,.2f}")
    col2.metric("Expenses", f"${total_expenses:,.2f}")
    col3.metric("Remaining Balance", f"${balance:,.2f}")

    if not expense_tx.empty:
        st.subheader("Expenses by Category")
        fig, ax = plt.subplots()
        expense_tx.groupby("Category")["Amount"].sum().plot(kind="bar", ax=ax)
        st.pyplot(fig)

# ==============================
# BUDGET SETUP
# ==============================

st.header("📋 Monthly Budgets")

if not transactions.empty:
    budget_month = st.selectbox("Budget Month", months, key="budget_month")

    with st.form("budget_form"):
        budget_category = st.text_input("Category")
        budget_amount = st.number_input("Budget Amount", min_value=0.0)
        submit_budget = st.form_submit_button("Save Budget")

        if submit_budget:
            df = load_data("Budgets")
            new_row = pd.DataFrame([[budget_month, budget_category, budget_amount]],
                                   columns=["Month", "Category", "Budget"])
            df = pd.concat([df, new_row], ignore_index=True)
            save_data(df, "Budgets")
            st.success("Budget saved!")

budgets_df = load_data("Budgets")

if not budgets_df.empty:
    edited_budgets = st.data_editor(budgets_df, num_rows="dynamic", use_container_width=True)
    if st.button("💾 Save Budget Changes"):
        save_data(edited_budgets, "Budgets")
        st.success("Budgets updated!")

# ==============================
# BUDGET VS ACTUAL
# ==============================

if not budgets_df.empty and not transactions.empty:
    st.header("📊 Budget vs Actual")

    month_budgets = budgets_df[budgets_df["Month"] == selected_month]

    if not month_budgets.empty:
        actuals = expense_tx.groupby("Category")["Amount"].sum().reset_index()

        comparison = pd.merge(month_budgets, actuals, on="Category", how="left").fillna(0)
        comparison["Variance"] = comparison["Budget"] - comparison["Amount"]

        st.dataframe(comparison, use_container_width=True)
        st.bar_chart(comparison.set_index("Category")[["Budget", "Amount"]])

# ==============================
# APPLY RECURRING ENGINE
# ==============================

st.header("⚙️ Apply Recurring Items to Month")

if not rules_df.empty and not transactions.empty:
    last_month = pd.Period(max(months), freq="M")
    next_month = str(last_month + 1)

    if next_month not in months:
        months.append(next_month)

    target_month = st.selectbox("Apply recurring to month", months, key="recurring_month")

    existing_keys = get_existing_recurring_keys(transactions, target_month)
    preview_rows = []

    for _, rule in rules_df.iterrows():
        if rule["Active"]:
            key = (target_month, rule["Name"], rule["Type"])
            if key not in existing_keys:
                preview_rows.append({
                    "Date": f"{target_month}-01",
                    "Type": rule["Type"],
                    "Name": rule["Name"],
                    "Category": rule["Category"],
                    "Amount": rule["Amount"]
                })

    preview_df = pd.DataFrame(preview_rows)

    if not preview_df.empty:
        st.dataframe(preview_df, use_container_width=True)
        confirm = st.checkbox("Confirm apply recurring items")

        if st.button("Apply Recurring Items") and confirm:
            for _, row in preview_df.iterrows():
                add_transaction(pd.to_datetime(row["Date"]), row["Type"], row["Name"], row["Category"], row["Amount"])
            st.success("Recurring items applied!")

# ==============================
# FORECASTING
# ==============================

st.header("🔮 Financial Forecast")

if not transactions.empty and not rules_df.empty:
    months_ahead = st.slider("Forecast months", 1, 12, 6)
    forecast_df = generate_forecast(transactions, rules_df, months_ahead)

    if not forecast_df.empty:
        st.dataframe(forecast_df, use_container_width=True)

        forecast_summary = (
            forecast_df.groupby(["Month", "Type"])["Amount"]
            .sum()
            .unstack(fill_value=0)
            .reset_index()
        )

        forecast_summary["Projected Balance"] = (
            forecast_summary.get("Income", 0) - forecast_summary.get("Expense", 0)
        )

        st.dataframe(forecast_summary, use_container_width=True)
        st.line_chart(forecast_summary.set_index("Month")["Projected Balance"])

# ==============================
# TRANSACTION LOG
# ==============================

st.header("📄 Transaction Log")

tx_log = load_data("Transactions")

if not tx_log.empty:
    tx_log["Date"] = pd.to_datetime(tx_log["Date"])

    edited_tx = st.data_editor(tx_log.sort_values("Date", ascending=False), use_container_width=True)

    if st.button("💾 Save Transaction Changes"):
        save_data(edited_tx, "Transactions")
        st.success("Transactions updated!")