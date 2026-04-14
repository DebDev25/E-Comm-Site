import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from database.db import get_dataframe

def train_demand_model(df_products, df_sales):
    """
    Trains a Random Forest Regressor to predict 30-day demand.
    Features: price, rating, units_sold_last_15d
    Target: The next 30 days demand is simulated based on historical data.
    """
    if df_sales.empty or df_products.empty:
        return None
        
    df_sales['timestamp'] = pd.to_datetime(df_sales['timestamp'])
    df_sales['product_id'] = pd.to_numeric(df_sales['product_id'], errors='coerce').fillna(0).astype(int)
    df_sales['units_sold'] = pd.to_numeric(df_sales['units_sold'], errors='coerce').fillna(0).astype(int)
    
    # Calculate velocity: total units sold
    velocity = df_sales.groupby('product_id')['units_sold'].sum().reset_index()
    velocity.rename(columns={'units_sold': 'historical_sales'}, inplace=True)
    
    # Merge with products
    df = pd.merge(df_products, velocity, left_on='id', right_on='product_id', how='left')
    df['historical_sales'] = df['historical_sales'].fillna(0)
    df['rating'] = df['rating'].fillna(3.5) # Default rating
    
    # We use a supervised approach. Let's assume next 30d demand correlates with:
    # 30-day demand = historical_sales * scaling_factor + random noise 
    # This is a mock target for the sake of the exercise.
    # A real system would have longitudinal data.
    
    # Let's engineer features
    X = df[['price', 'rating', 'historical_sales']]
    
    # Create a synthetic target for training so the RF has something to learn
    # High rating & lower price & high historical sales = Higher demand
    y = (df['historical_sales'] * 1.5) + (df['rating'] * 10) - (df['price'] * 0.05)
    y = y.clip(lower=0)
    
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X, y)
    
    return model

def predict_demand(model, df_products, df_sales):
    """
    Predicts the future demand for each product.
    Returns a DataFrame with product_id and predicted_30d_demand.
    """
    if model is None or df_products.empty:
        return pd.DataFrame(columns=['product_id', 'predicted_30d_demand'])
        
    df_sales['timestamp'] = pd.to_datetime(df_sales['timestamp'])
    df_sales['product_id'] = pd.to_numeric(df_sales['product_id'], errors='coerce').fillna(0).astype(int)
    df_sales['units_sold'] = pd.to_numeric(df_sales['units_sold'], errors='coerce').fillna(0).astype(int)
    
    # Current velocity feature
    velocity = df_sales.groupby('product_id')['units_sold'].sum().reset_index()
    velocity.rename(columns={'units_sold': 'historical_sales'}, inplace=True)
    
    df = pd.merge(df_products, velocity, left_on='id', right_on='product_id', how='left')
    df['historical_sales'] = df['historical_sales'].fillna(0)
    df['rating'] = df['rating'].fillna(3.5)
    
    X_pred = df[['price', 'rating', 'historical_sales']]
    
    predictions = model.predict(X_pred)
    
    res = pd.DataFrame({
        'product_id': df['id'],
        'predicted_30d_demand': predictions.round(0).astype(int)
    })
    
    return res
