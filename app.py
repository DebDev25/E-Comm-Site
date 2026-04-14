import streamlit as st
import os

# Initialize app layout and config
st.set_page_config(
    page_title="Smart Retail Platform",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Setup basic session states if they don't exist
if 'user_email' not in st.session_state:
    st.session_state['user_email'] = 'user1@example.com' # Default mock user
if 'role' not in st.session_state:
    st.session_state['role'] = 'customer'
if 'cart' not in st.session_state:
    st.session_state['cart'] = []

# Load custom CSS
try:
    with open('styles/main.css') as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
except FileNotFoundError:
    pass

st.title("🛍️ Smart Retail Operations Platform")

st.markdown("""
Welcome to the AI-Driven E-Commerce & Strategic Operations Platform.
Please sign in by entering your email.
""")

from database.db import get_dataframe, hash_password

st.subheader("Sign In")
email_input = st.text_input("User Email", st.session_state['user_email'])
password_input = st.text_input("Password", type="password")

if st.button("Login"):
    # Check if DB exists
    import os
    if not os.path.exists('database/ecommerce.db'):
        st.warning("Database not found. Bootstrapping mock data...")
        from database.data_generator import build_mock_data
        build_mock_data()
        st.success("Database created successfully! Please try logging in again.")
    else:
        df_users = get_dataframe("SELECT * FROM users WHERE email = ?", params=(email_input,))
        if not df_users.empty:
            stored_hash = df_users.iloc[0]['password']
            if stored_hash == hash_password(password_input):
                role = df_users.iloc[0]['role']
                st.session_state['user_email'] = email_input
                st.session_state['role'] = role
                st.success(f"Logged in successfully as {email_input} ({role})")
                st.rerun()
            else:
                st.error("Invalid password provided. Please try again.")
        else:
            st.error("User not found in system. Please enter a valid email.")

st.markdown(f"**Current User:** {st.session_state['user_email']} | **Role:** {st.session_state['role']}")

st.info("Navigate to `1_Store` to experience AI Search and Recommendations. Switch to an admin or manager to view other dashboards.")
