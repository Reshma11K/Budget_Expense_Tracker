import streamlit as st

# ==============================
# 💰 INCOME FILTERS
# ==============================
def apply_income_filters(df):
    if df.empty:
        return df

    st.markdown("### 🔎 Filters")

    col1, col2, col3 = st.columns(3)

    source_filter = col1.text_input("Search Source")

    category_filter = col2.multiselect(
        "Category",
        options=sorted(df["category"].dropna().unique())
    )

    amount_range = col3.slider(
        "Amount Range",
        float(df["amount"].min()),
        float(df["amount"].max()),
        (float(df["amount"].min()), float(df["amount"].max()))
    )

    date_range = st.date_input(
        "Date Range",
        value=(df["date"].min(), df["date"].max())
    )

    # APPLY
    if source_filter:
        df = df[df["source"].str.contains(source_filter, case=False, na=False)]

    if category_filter:
        df = df[df["category"].isin(category_filter)]

    df = df[
        (df["amount"] >= amount_range[0]) &
        (df["amount"] <= amount_range[1])
    ]

    if len(date_range) == 2:
        df = df[
            (df["date"] >= str(date_range[0])) &
            (df["date"] <= str(date_range[1]))
        ]

    return df


# ==============================
# 🔁 RECURRING FILTERS
# ==============================
def apply_recurring_filters(df):
    if df.empty:
        return df

    st.markdown("### 🔎 Filters")

    col1, col2, col3 = st.columns(3)

    name_filter = col1.text_input("Search Name")

    category_filter = col2.multiselect(
        "Category",
        options=sorted(df["category"].dropna().unique())
    )

    payment_filter = col3.multiselect(
        "Payment Method",
        options=sorted(df["payment_method"].dropna().unique())
    )

    amount_range = st.slider(
        "Amount Range",
        float(df["amount"].min()),
        float(df["amount"].max()),
        (float(df["amount"].min()), float(df["amount"].max()))
    )

    # APPLY
    if name_filter:
        df = df[df["name"].str.contains(name_filter, case=False, na=False)]

    if category_filter:
        df = df[df["category"].isin(category_filter)]

    if payment_filter:
        df = df[df["payment_method"].isin(payment_filter)]

    df = df[
        (df["amount"] >= amount_range[0]) &
        (df["amount"] <= amount_range[1])
    ]

    return df
# ==============================
# 🔁 Expenses FILTERS
# ==============================

def apply_expense_filters(df):
    if df.empty:
        return df

    st.markdown("### 🔎 Filters")

    col1, col2, col3, col4 = st.columns(4)

    # 🔍 Name search
    name_filter = col1.text_input("Search Name")

    # 📂 Category
    category_filter = col2.multiselect(
        "Category",
        options=sorted(df["category"].dropna().unique())
    )

    # 💳 Payment
    payment_filter = col3.multiselect(
        "Payment",
        options=sorted(df["payment_method"].dropna().unique())
    )

    # 💰 Amount range
    min_amt, max_amt = col4.slider(
        "Amount Range",
        float(df["amount"].min()),
        float(df["amount"].max()),
        (float(df["amount"].min()), float(df["amount"].max()))
    )

    # 📅 Date range
    date_range = st.date_input(
        "Date Range",
        value=(df["date"].min(), df["date"].max())
    )

    # ======================
    # APPLY FILTERS
    # ======================
    if name_filter:
        df = df[df["name"].str.contains(name_filter, case=False, na=False)]

    if category_filter:
        df = df[df["category"].isin(category_filter)]

    if payment_filter:
        df = df[df["payment_method"].isin(payment_filter)]

    df = df[(df["amount"] >= min_amt) & (df["amount"] <= max_amt)]

    if len(date_range) == 2:
        df = df[
            (df["date"] >= str(date_range[0])) &
            (df["date"] <= str(date_range[1]))
        ]

    return df