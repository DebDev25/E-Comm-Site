import streamlit as st
import pandas as pd
from database.db import execute_query
import uuid

st.set_page_config(page_title="Shopping Cart", layout="wide")

try:
    with open('styles/main.css') as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
except FileNotFoundError:
    pass

st.title("🛒 Your Shopping Cart")

cart = st.session_state.get('cart', [])

if not cart:
    st.info("Your cart is empty.")
    if st.button("Go Shopping"):
        st.switch_page("pages/1_Store.py")
    st.stop()

# Convert cart items to dataframe for easy display
df_cart = pd.DataFrame(cart)
df_cart['Total'] = df_cart['price'] * df_cart['units']

st.dataframe(df_cart[['name', 'price', 'units', 'Total']], use_container_width=True)

total_cost = df_cart['Total'].sum()
st.markdown(f"### Grand Total: **${total_cost:.2f}**")

user_email = st.session_state.get('user_email', 'guest@example.com')
st.markdown(f"**Checkout as:** {user_email}")

if st.button("💳 Proceed to Checkout", type="primary"):
    order_id = str(uuid.uuid4())[:8]
    sales_data = []
    
    # Needs to deduct stock and add to sales
    for item in cart:
        pid = item['product_id']
        units = item['units']
        sales_data.append((order_id, pid, units, user_email))
        
        # Deduct from stock
        query_stock = "UPDATE products SET stock = MAX(0, stock - ?) WHERE id = ?"
        execute_query(query_stock, (units, pid))
        
        # Insert sale
        query_sale = "INSERT INTO sales (order_id, product_id, units_sold, user_email) VALUES (?, ?, ?, ?)"
        execute_query(query_sale, (order_id, pid, units, user_email))
    
    st.success(f"Checkout successful! Order ID: **{order_id}**")
    st.balloons()
    
    # Clear cart
    st.session_state['cart'] = []
    st.cache_data.clear() # clear product caches to refetch stock and sales
    
    # Automatically switch back to store after success or provide button
    if st.button("Return to Store"):
        st.switch_page("pages/1_Store.py")
