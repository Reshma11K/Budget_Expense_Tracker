import streamlit as st


def sidebar():
    with st.sidebar:
        st.markdown("## 🏠 Budget App")
        st.caption("Personal Finance Dashboard")

        st.divider()

        # 👤 User
        st.markdown(f"**👤 {st.session_state.get('user', 'User')}**")

        if st.button("🚪 Logout", use_container_width=True, key="logout_button"):
            st.session_state["token"] = None
            st.session_state["user"] = None
            st.rerun()

        st.divider()

        # 📍 Navigation
        st.markdown("### 📍 Navigation")

        menu = st.radio(
            "",
            [
                ("📊 Dashboard", "Dashboard"),
                ("💰 Income", "Income"),
                ("🧾 Expenses", "Expenses"),
                ("🔁 Recurring", "Recurring"),
                ("📋 Budget", "Budget"),
                ("📄 Log", "Log"),
            ],
            format_func=lambda x: x[0],
            key="main_navigation"
        )[1]

        st.divider()
        st.caption("v1.0 • FastAPI + Streamlit")

    return menu