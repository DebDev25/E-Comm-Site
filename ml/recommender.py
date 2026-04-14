import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from database.db import get_dataframe

def get_product_similarity_matrix(df):
    """
    Computes a Content-Based similarity matrix using TF-IDF on product descriptions and categories.
    """
    if df.empty or 'description' not in df.columns or 'category' not in df.columns:
        return pd.DataFrame()
        
    df['content'] = df['category'] + " " + df['description']
    df['content'] = df['content'].fillna("")
    
    tfidf = TfidfVectorizer(stop_words='english')
    tfidf_matrix = tfidf.fit_transform(df['content'])
    
    cosine_sim = cosine_similarity(tfidf_matrix, tfidf_matrix)
    
    # Return as a DataFrame to easily lookup by product ID
    sim_df = pd.DataFrame(cosine_sim, index=df['id'], columns=df['id'])
    return sim_df

def get_similar_items(product_id, sim_matrix, df, top_n=4):
    """
    Returns top N similar products based on the content similarity matrix.
    """
    if product_id not in sim_matrix.index:
        return pd.DataFrame()
        
    sim_scores = sim_matrix[product_id]
    
    # Sort and exclude the item itself
    similar_ids = sim_scores.sort_values(ascending=False).iloc[1:top_n+1].index
    
    return df[df['id'].isin(similar_ids)]

def get_nlp_search_results(query, df, top_n=5):
    """
    NLP Semantic Search mapping a query to product descriptions.
    """
    if not query.strip() or df.empty:
        return pd.DataFrame()
        
    df['content'] = df['category'] + " " + df['name'] + " " + df['description'].fillna("")
    
    # Add query to end of corpus to vectorize it in the same space
    corpus = df['content'].tolist()
    corpus.append(query)
    
    tfidf = TfidfVectorizer(stop_words='english')
    tfidf_matrix = tfidf.fit_transform(corpus)
    
    # Cosine sim of query (last row) against all other rows
    cosine_sim = cosine_similarity(tfidf_matrix[-1], tfidf_matrix[:-1]).flatten()
    
    # Get top N indices
    top_indices = cosine_sim.argsort()[-top_n:][::-1]
    
    # Filter where similarity is not 0
    results = df.iloc[top_indices]
    results = results[cosine_sim[top_indices] > 0]
    
    return results

def get_collaborative_recommendations(user_email, df_products, df_ratings, top_n=4):
    """
    User-to-Item Collaborative Filtering (Memory-based).
    Returns recommended products for a user based on similarities to other users.
    If no history, returns popular items.
    """
    if df_ratings.empty or user_email not in df_ratings['user_email'].unique():
        # Fallback to general popular or highest rated items
        if not df_products.empty:
            return df_products.sort_values(by='rating', ascending=False).head(top_n)
        return pd.DataFrame()
        
    # Create User-Item matrix
    matrix = df_ratings.pivot_table(index='user_email', columns='product_id', values='rating').fillna(0)
    
    user_ratings = matrix.loc[user_email].values.reshape(1, -1)
    
    # Calculate similarity between target user and all others
    user_similarities = cosine_similarity(user_ratings, matrix)[0]
    
    # Weight ratings of all users by their similarity to target user
    weighted_ratings = matrix.T.dot(user_similarities)
    
    # Normalize by sum of similarities
    sum_similarities = np.abs(user_similarities).sum()
    if sum_similarities > 0:
        predicted_ratings = weighted_ratings / sum_similarities
    else:
        predicted_ratings = weighted_ratings
        
    # Convert to Series for easy filtering
    predictions = pd.Series(predicted_ratings, index=matrix.columns)
    
    # Filter out items already rated by user
    user_rated_items = matrix.loc[user_email]
    predictions = predictions[user_rated_items == 0]
    
    # Get top N recommended item IDs
    recommended_ids = predictions.sort_values(ascending=False).head(top_n).index
    
    return df_products[df_products['id'].isin(recommended_ids)]

def get_market_basket(product_id, df_sales, df_products, top_n=4):
    """
    Co-occurrence based Market Basket Analysis.
    Finds products frequently bought in the same order_id as the given product.
    """
    if df_sales.empty:
        return pd.DataFrame()
        
    # Get all order_ids that contain the target product
    target_orders = df_sales[df_sales['product_id'] == product_id]['order_id'].unique()
    
    if len(target_orders) == 0:
        return pd.DataFrame()
        
    # Filter sales to only those orders
    basket_sales = df_sales[df_sales['order_id'].isin(target_orders)]
    
    # Count occurrences of other products in these orders
    co_occurrences = basket_sales[basket_sales['product_id'] != product_id]['product_id'].value_counts()
    
    if co_occurrences.empty:
        return pd.DataFrame()
        
    freq_ids = co_occurrences.head(top_n).index
    
    return df_products[df_products['id'].isin(freq_ids)]
