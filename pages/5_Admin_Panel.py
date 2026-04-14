import streamlit as st
import pandas as pd
from database.db import get_dataframe, execute_query, hash_password

st.set_page_config(page_title="Admin Panel", layout="wide", page_icon="🛡️")

try:
    with open('styles/main.css') as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
except FileNotFoundError:
    pass

st.title("🛡️ Admin Panel")

# Security check
if st.session_state.get('role') != 'administrator':
    st.error("Access Denied: You must be an Administrator to view this page.")
    if st.button("Go Home"):
        st.switch_page("app.py")
    st.stop()
    
st.markdown("Manage system access and roles here.")

# Fetch all users
@st.cache_data(ttl=5)
def load_users():
    return get_dataframe("SELECT id, email, role, created_at FROM users")

df_users = load_users()

c1, c2 = st.columns([1, 2])

with c1:
    st.subheader("Add New User")
    with st.form("add_user_form", clear_on_submit=True):
        new_email = st.text_input("User Email")
        new_pass = st.text_input("Initial Password", type="password")
        new_role = st.selectbox("Role", ["customer", "manager", "administrator"])
        submitted = st.form_submit_button("Add User")
        
        if submitted:
            if not new_email.strip() or "@" not in new_email:
                st.error("Please provide a valid email.")
            elif not new_pass.strip():
                st.error("Please provide an initial password.")
            else:
                try:
                    hashed_pass = hash_password(new_pass)
                    execute_query("INSERT INTO users (email, password, role) VALUES (?, ?, ?)", (new_email.strip(), hashed_pass, new_role))
                    st.success(f"Added {new_email} as {new_role}!")
                    st.cache_data.clear()
                    st.rerun()
                except Exception as e:
                    st.error(f"Error adding user (might already exist): {e}")

with c2:
    st.subheader("Existing Users")
    st.dataframe(df_users, use_container_width=True, hide_index=True)
    
st.divider()

st.subheader("Modify User Roles")

target_email = st.selectbox("Select User to Modify", df_users['email'].tolist())
if target_email:
    current_role = df_users[df_users['email'] == target_email].iloc[0]['role']
    st.write(f"Current role for **{target_email}**: `{current_role}`")
    
    col_update, col_padding = st.columns([1, 2])
    with col_update:
        update_role = st.selectbox("Assign New Role", ["customer", "manager", "administrator"], 
                                   index=["customer", "manager", "administrator"].index(current_role))
        
        if st.button("Update Role", type="primary"):
            if target_email == st.session_state.get('user_email') and update_role != 'administrator':
                st.warning("You cannot demote yourself. Please have another admin do it if necessary.")
            else:
                try:
                    execute_query("UPDATE users SET role = ? WHERE email = ?", (update_role, target_email))
                    st.success(f"Successfully updated {target_email} to {update_role}!")
                    # If altering current session user role, force it to update locally too:
                    if target_email == st.session_state.get('user_email'):
                        st.session_state['role'] = update_role
                    st.cache_data.clear()
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to update role: {e}")
