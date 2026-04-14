import streamlit as st
import pandas as pd
from database.db import get_dataframe, execute_query
from ml.recommender import get_product_similarity_matrix, get_similar_items, get_market_basket
import base64

def get_base64_image(path_or_url):
    if not str(path_or_url).startswith("assets/"):
        return path_or_url
    try:
        with open(path_or_url, "rb") as f:
            encoded = base64.b64encode(f.read()).decode()
        return f"data:image/png;base64,{encoded}"
    except:
        return path_or_url

st.set_page_config(page_title="Product Details", layout="wide")

try:
    with open('styles/main.css') as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
except FileNotFoundError:
    pass

# Check if a product was selected
if 'selected_product' not in st.session_state:
    st.warning("Please select a product from the Store first.")
    if st.button("Go to Store"):
        st.switch_page("pages/1_Store.py")
    st.stop()

product_id = st.session_state['selected_product']

# Load data
@st.cache_data(ttl=60)
def load_product_data(pid):
    df_product = get_dataframe(f"SELECT * FROM products WHERE id = {pid} AND is_active = 1")
    df_all_products = get_dataframe("SELECT * FROM products WHERE is_active = 1")
    df_sales = get_dataframe("SELECT * FROM sales")
    return df_product, df_all_products, df_sales

df_p, df_all, df_sales = load_product_data(product_id)

if df_p.empty:
    st.error("Product not found.")
    st.stop()

product = df_p.iloc[0]

# UI Layout
if st.button("← Back to Store"):
    st.switch_page("pages/1_Store.py")

col1, col2 = st.columns([1, 2])

with col1:
    st.image(product['image_url'], use_container_width=True)

with col2:
    st.markdown(f"<div class='product-category'>{product['category']}</div>", unsafe_allow_html=True)
    st.title(product['name'])
    st.markdown(f"**Description:** {product['description']}")
    st.markdown(f"## ${product['price']:.2f}")
    
    st.markdown(f"**Current Rating:** ⭐ {product['rating']} / 5.0")
    
    stock_status = "In Stock" if product['stock'] > product['reorder_point'] else "Low Stock" if product['stock'] > 0 else "Out of Stock"
    stock_color = "green" if stock_status == "In Stock" else "orange" if stock_status == "Low Stock" else "red"
    st.markdown(f"**Availability:** <span style='color:{stock_color}; font-weight:bold;'>{stock_status} ({product['stock']} units)</span>", unsafe_allow_html=True)
    
    # Add to Cart
    units = st.number_input("Quantity", min_value=1, max_value=max(1, product['stock']), value=1)
    if st.button("🛒 Add to Cart"):
        cart_item = {
            'product_id': product['id'],
            'name': product['name'],
            'price': product['price'],
            'units': units,
            'image_url': product['image_url']
        }
        st.session_state['cart'].append(cart_item)
        st.success(f"Added {units} x {product['name']} to cart!")
    
    st.divider()
    
    # Rate Product functionality
    st.subheader("Rate this Product")
    user_email = st.session_state.get('user_email', 'guest@example.com')
    rating = st.slider("Select Rating", 1, 5, 5)
    if st.button("Submit Rating"):
        try:
            # Upsert logic for sqlite: handle duplicate user_email, product_id pair
            query = """
            INSERT INTO user_ratings (user_email, product_id, rating) 
            VALUES (?, ?, ?)
            ON CONFLICT(user_email, product_id) 
            DO UPDATE SET rating=excluded.rating, timestamp=CURRENT_TIMESTAMP
            """
            execute_query(query, (user_email, int(product_id), int(rating)))
            
            # Recalculate average rating for the product and update products table
            avg_query = """
            UPDATE products 
            SET rating = (SELECT ROUND(AVG(rating), 1) FROM user_ratings WHERE product_id = ?)
            WHERE id = ?
            """
            execute_query(avg_query, (int(product_id), int(product_id)))
            
            st.success("Rating submitted successfully! Thank you.")
            st.cache_data.clear() # Clear cache to show new rating on reload
            st.rerun()
        except Exception as e:
            st.error(f"Error submitting rating: {e}")

st.divider()

# Helper to render small card
def render_small_card(row, section_prefix=""):
    img_src = get_base64_image(row['image_url'])
    card = f"""
    <div style="border: 1px solid #ddd; padding: 10px; border-radius: 8px; text-align: center;">
        <img src="{img_src}" style="max-height: 100px; object-fit: contain;">
        <div style="font-size: 0.9rem; font-weight: bold; margin-top: 8px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{row['name']}</div>
        <div style="color: #2e7d32; font-weight: bold;">${row['price']:.2f}</div>
    </div>
    """
    st.markdown(card, unsafe_allow_html=True)
    if st.button("View", key=f"{section_prefix}rec_view_{row['id']}"):
        st.session_state['selected_product'] = row['id']
        st.rerun()

col_mba, col_cbf = st.columns(2)

with col_mba:
    st.subheader("🔗 Frequently Bought Together")
    fbt = get_market_basket(product_id, df_sales.copy(), df_all.copy(), top_n=3)
    if not fbt.empty:
        c = st.columns(3)
        for i, (_, row) in enumerate(fbt.iterrows()):
            with c[i % 3]:
                render_small_card(row, section_prefix="fbt_")
    else:
        st.info("Not enough data to determine frequent pairings.")

with col_cbf:
    st.subheader("🔍 Similar Items")
    sim_mat = get_product_similarity_matrix(df_all.copy())
    similar = get_similar_items(product_id, sim_mat, df_all.copy(), top_n=3)
    
    if not similar.empty:
        c = st.columns(3)
        for i, (_, row) in enumerate(similar.iterrows()):
            with c[i % 3]:
                render_small_card(row, section_prefix="sim_")
    else:
        st.info("No similar items found.")
