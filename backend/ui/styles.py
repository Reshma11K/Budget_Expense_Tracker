def apply_sidebar_style():
    import streamlit as st

    st.markdown("""
    <style>
    [data-testid="stSidebar"] {
        background-color: #0f172a;
        border-right: 1px solid #1f2937;
    }

    [data-testid="stSidebar"] * {
        color: #e5e7eb;
    }

    div[role="radiogroup"] {
        gap: 6px;
    }

    div[role="radiogroup"] > label {
        padding: 10px 12px;
        border-radius: 10px;
        margin-bottom: 4px;
        transition: all 0.2s ease;
    }

    div[role="radiogroup"] > label:hover {
        background-color: #1e293b;
        cursor: pointer;
    }

    div[role="radiogroup"] > label[data-selected="true"] {
        background: linear-gradient(90deg, #2563eb, #1d4ed8);
        color: white;
        font-weight: 600;
    }
    </style>
    """, unsafe_allow_html=True)