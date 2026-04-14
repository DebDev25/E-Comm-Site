import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
from database.db import get_dataframe, execute_query
from ml.demand_prediction import train_demand_model, predict_demand

st.set_page_config(page_title="Manager Dashboard", layout="wide", page_icon="📈")

try:
    with open('styles/main.css') as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
except FileNotFoundError:
    pass

st.title("📈 Strategic Operations Dashboard")

if st.session_state.get('role') != 'manager':
    st.error("Access Denied: You must be a Manager to view this page.")
    if st.button("Change Role"):
        st.switch_page("app.py")
    st.stop()

@st.cache_data(ttl=60)
def load_all_data():
    df_products = get_dataframe("SELECT * FROM products")
    df_sales = get_dataframe("SELECT * FROM sales")
    return df_products, df_sales

df_products, df_sales = load_all_data()

if df_sales.empty:
    st.warning("No sales data available yet.")
    st.stop()

# --- Key Metrics ---
# Enrich sales with product data
sales_enriched = pd.merge(df_sales, df_products, left_on='product_id', right_on='id')
sales_enriched['revenue'] = sales_enriched['units_sold'] * sales_enriched['price']
sales_enriched['cost_total'] = sales_enriched['units_sold'] * sales_enriched['cost']
sales_enriched['profit'] = sales_enriched['revenue'] - sales_enriched['cost_total']

total_rev = sales_enriched['revenue'].sum()
total_profit = sales_enriched['profit'].sum()
margin = (total_profit / total_rev) * 100 if total_rev > 0 else 0
orders = sales_enriched['order_id'].nunique()

c1, c2, c3, c4 = st.columns(4)
c1.markdown(f"<div class='metric-container'><div class='metric-title'>Total Revenue</div><div class='metric-value'>${total_rev:,.0f}</div></div>", unsafe_allow_html=True)
c2.markdown(f"<div class='metric-container'><div class='metric-title'>Total Profit</div><div class='metric-value'>${total_profit:,.0f}</div></div>", unsafe_allow_html=True)
c3.markdown(f"<div class='metric-container'><div class='metric-title'>Profit Margin</div><div class='metric-value'>{margin:.1f}%</div></div>", unsafe_allow_html=True)
c4.markdown(f"<div class='metric-container'><div class='metric-title'>Total Orders</div><div class='metric-value'>{orders:,}</div></div>", unsafe_allow_html=True)

st.divider()

# --- Performance Analytics ---
col_chart1, col_chart2 = st.columns(2)

with col_chart1:
    st.subheader("Revenue by Category")
    cat_perf = sales_enriched.groupby('category')['revenue'].sum().reset_index()
    chart = alt.Chart(cat_perf).mark_bar().encode(
        x=alt.X('revenue:Q', title='Revenue ($)'),
        y=alt.Y('category:N', sort='-x', title='Category'),
        color=alt.Color('category:N', legend=None),
        tooltip=['category', 'revenue']
    ).properties(height=300)
    st.altair_chart(chart, use_container_width=True)

with col_chart2:
    st.subheader("Sales Velocity (Last 30 Days Simulation)")
    sales_enriched['date'] = pd.to_datetime(sales_enriched['timestamp']).dt.date
    daily_sales = sales_enriched.groupby('date')['units_sold'].sum().reset_index()
    line = alt.Chart(daily_sales).mark_line(color='#ff7f0e').encode(
        x='date:T',
        y='units_sold:Q',
        tooltip=['date', 'units_sold']
    ).properties(height=300)
    st.altair_chart(line, use_container_width=True)

st.divider()

# --- AI Inventory Forecasting & Strategic Reordering ---
st.subheader("🧠 AI Inventory Forecasting")

@st.cache_resource(ttl=3600)
def get_demand_model():
    return train_demand_model(df_products.copy(), df_sales.copy())

model = get_demand_model()

if model is not None:
    predictions = predict_demand(model, df_products.copy(), df_sales.copy())
    
    # Merge predictions into products
    inventory_df = pd.merge(df_products[['id', 'name', 'category', 'stock', 'reorder_point', 'lead_time_days']], predictions, left_on='id', right_on='product_id')
    
    # Action Alert Logic: Stock <= (Predicted Demand * fraction) + buffer
    # Since our mock demand is synthetic, we'll just define:
    # Danger If: Current Stock < Predicted 30d Demand
    
    def determine_action(row):
        safe_stock = row['predicted_30d_demand'] + row['lead_time_days'] * (row['predicted_30d_demand']/30.0)
        if row['stock'] <= 0:
            return "🚨 OUT OF STOCK"
        elif row['stock'] <= safe_stock * 0.5:
            return "🔴 Critical Reorder"
        elif row['stock'] <= safe_stock:
            return "🟡 Reorder Soon"
        else:
            return "✅ Healthy"
    
    inventory_df['Status'] = inventory_df.apply(determine_action, axis=1)
    
    # Display table highlighting critical items
    critical_items = inventory_df[inventory_df['Status'].str.contains("🚨|🔴")]
    
    if not critical_items.empty:
        st.warning(f"**Alert:** {len(critical_items)} items require immediate attention based on AI forecasting.")
        st.dataframe(critical_items[['name', 'category', 'stock', 'predicted_30d_demand', 'lead_time_days', 'Status']], use_container_width=True)
    else:
        st.success("All inventory levels are healthy based on AI forecasting.")
        
    with st.expander("View Full Inventory Forecast"):
        st.dataframe(inventory_df[['name', 'category', 'stock', 'predicted_30d_demand', 'lead_time_days', 'Status']], use_container_width=True)
else:
    st.error("Failed to train demand model via Random Forest.")

st.divider()

# --- Catalog Management (CRUD) ---
st.subheader("🛍️ Catalog Management")

tab_add, tab_remove = st.tabs(["Add New Product", "Remove Product"])

with tab_add:
    with st.form("add_product_form", clear_on_submit=True):
        col_f1, col_f2 = st.columns(2)
        p_name = col_f1.text_input("Product Name")
        p_cat = col_f2.selectbox("Category", ["Laptops", "Smartphones", "Headphones", "Monitors", "Keyboards", "Other"])
        
        col_f3, col_f4, col_f5 = st.columns(3)
        p_price = col_f3.number_input("Retail Price ($)", min_value=1.0, value=99.99)
        p_cost = col_f4.number_input("Unit Cost ($)", min_value=1.0, value=50.0)
        p_stock = col_f5.number_input("Initial Stock", min_value=0, value=50)
        
        col_f6, col_f7 = st.columns(2)
        p_reorder = col_f6.number_input("Reorder Threshold", min_value=0, value=10)
        p_lead = col_f7.number_input("Supplier Lead Time (Days)", min_value=1, value=7)
        
        p_img = st.text_input("Image URL", placeholder="e.g. https://images.unsplash.com/photo-123456")
        p_desc = st.text_area("Product Description")
        
        submitted_add = st.form_submit_button("Add to Catalog")
        
        if submitted_add:
            if not p_name.strip() or not p_img.strip() or not p_desc.strip():
                st.error("Please fill out all required text fields (Name, Image URL, Description).")
            else:
                try:
                    execute_query('''
                        INSERT INTO products (name, category, price, cost, stock, reorder_point, lead_time_days, rating, description, image_url, is_active)
                        VALUES (?, ?, ?, ?, ?, ?, ?, 0.0, ?, ?, 1)
                    ''', (p_name.strip(), p_cat, p_price, p_cost, p_stock, p_reorder, p_lead, p_desc.strip(), p_img.strip()))
                    st.success(f"Successfully added '{p_name}' to the catalog!")
                    st.cache_data.clear()
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to add product: {e}")

with tab_remove:
    active_products = df_products[df_products['is_active'] == 1] if 'is_active' in df_products.columns else df_products
    
    if not active_products.empty:
        # Create a dictionary mapping names to IDs for the selectbox
        prod_map = {f"{row['name']} (ID: {row['id']})": row['id'] for _, row in active_products.iterrows()}
        selected_to_remove = st.selectbox("Select Product to Remove", options=list(prod_map.keys()))
        
        if st.button("🚨 Remove from Catalog", type="primary"):
            target_id = prod_map[selected_to_remove]
            try:
                execute_query("UPDATE products SET is_active = 0 WHERE id = ?", (target_id,))
                st.success(f"Product '{selected_to_remove}' has been successfully removed from public storefront visibility.")
                st.info("Note: Historical revenue and sales data for this item has been securely preserved for analytics calculations.")
                st.cache_data.clear()
                st.rerun()
            except Exception as e:
                st.error(f"Failed to remove product: {e}")
    else:
        st.info("No active products available to remove.")
