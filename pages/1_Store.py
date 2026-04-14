import streamlit as st
import pandas as pd
from database.db import get_dataframe
from ml.recommender import get_nlp_search_results, get_collaborative_recommendations
import os

st.set_page_config(page_title="Storefront", layout="wide")

# Ensure CSS is loaded (Streamlit reruns scripts independently)
try:
    with open('styles/main.css') as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
except FileNotFoundError:
    pass

st.title("🛒 AI-Enhanced Storefront")

# Data loading with caching
@st.cache_data(ttl=600)
def load_data():
    df_products = get_dataframe("SELECT * FROM products WHERE is_active = 1")
    df_ratings = get_dataframe("SELECT * FROM user_ratings")
    return df_products, df_ratings

df_products, df_ratings = load_data()

if df_products.empty:
    st.warning("No products found. Please ensure the database is initialized in app.py.")
    st.stop()

import base64

def get_base64_image(path_or_url):
    if not str(path_or_url).startswith("assets/"):
        return path_or_url
    try:
        with open(path_or_url, "rb") as f:
            encoded = base64.b64encode(f.read()).decode()
        return f"data:image/png;base64,{encoded}"
    except Exception:
        return path_or_url

# Helper to render product card
def render_product_card(row, key_suffix=""):
    stock_class = "stock-in" if row['stock'] > row['reorder_point'] else "stock-low"
    stock_text = "In Stock" if row['stock'] > row['reorder_point'] else "Low Stock"
    if row['stock'] <= 0:
        stock_class = "stock-out"
        stock_text = "Out of Stock"
        
    img_src = get_base64_image(row['image_url'])
    card_html = f"""
    <div class="product-card">
        <div class="product-img-container">
            <img src="{img_src}" class="product-img" alt="{row['name']}">
        </div>
        <div class="product-category">{row['category']}</div>
        <div class="product-title">{row['name']}</div>
        <div class="product-rating">⭐ {row['rating']} / 5.0</div>
        <div class="stock-badge {stock_class}">{stock_text}</div>
        <div class="product-price">${row['price']:.2f}</div>
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)
    if st.button(f"View Details", key=f"view_{row['id']}_{key_suffix}"):
        st.session_state['selected_product'] = row['id']
        st.switch_page("pages/2_Product_Details.py")

# --- AI Shopping Assistant ---
st.subheader("🤖 AI Shopping Assistant")
st.markdown("Describe what you're looking for, or any problem you want to solve, and our AI will find the best match!")
query = st.text_input("e.g., 'I need a fast computer for work and gaming'")

if query:
    st.write(f"Searching for: *{query}*")
    results = get_nlp_search_results(query, df_products.copy(), top_n=4)
    if not results.empty:
        cols = st.columns(4)
        for i, (_, row) in enumerate(results.iterrows()):
            with cols[i % 4]:
                render_product_card(row, key_suffix=f"search_{i}")
    else:
        st.info("No matches found. Try different keywords.")
    st.divider()

# --- Personalized Recommendations ---
st.subheader(f"✨ Recommended for You ({st.session_state.get('user_email', 'Guest')})")
recs = get_collaborative_recommendations(st.session_state.get('user_email', ''), df_products.copy(), df_ratings.copy(), top_n=4)

if not recs.empty:
    cols = st.columns(4)
    for i, (_, row) in enumerate(recs.iterrows()):
        with cols[i % 4]:
            render_product_card(row, key_suffix=f"recs_{i}")
else:
    st.info("Not enough data to personalize yet. Here are some popular items:")
    popular = df_products.sort_values(by='rating', ascending=False).head(4)
    cols = st.columns(4)
    for i, (_, row) in enumerate(popular.iterrows()):
        with cols[i % 4]:
            render_product_card(row, key_suffix=f"pop_{i}")

st.divider()

# --- All Products Catalog ---
st.subheader("Browse All Products")

# Simple category filter
categories = ["All Categories"] + df_products['category'].unique().tolist()
selected_cat = st.selectbox("Filter by Category", categories)

filtered_df = df_products if selected_cat == "All Categories" else df_products[df_products['category'] == selected_cat]

# Grid layout
rows = [filtered_df.iloc[i:i+4] for i in range(0, len(filtered_df), 4)]
for row_idx, r in enumerate(rows):
    cols = st.columns(4)
    for i, (_, row) in enumerate(r.iterrows()):
        with cols[i]:
            render_product_card(row, key_suffix=f"cat_{row_idx}_{i}")
