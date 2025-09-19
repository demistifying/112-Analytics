# main.py
import streamlit as st
from modules.login import check_credentials
import app  # your dashboard code

st.set_page_config(page_title="Goa Police Dashboard", layout="wide")

# Initialize session state for login
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user = None

# If not logged in → show login form
if not st.session_state.logged_in:
    st.title("🔐 Goa Police Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    login_btn = st.button("Login")

    if login_btn:
        user = check_credentials(username, password)
        if user:
            st.session_state.logged_in = True
            st.session_state.user = user
            st.success(f"Welcome, {user['username']} ({user['rank']})!")
            st.rerun()  # 🔑 reload to show dashboard
        else:
            st.error("Invalid username or password.")

else:
    # Already logged in → show dashboard
    st.sidebar.success(f"👮 Logged in as {st.session_state.user['username']} ({st.session_state.user['rank']})")

    # Add logout button
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.user = None
        st.experimental_rerun()

    # Run your existing dashboard
    app.run()
