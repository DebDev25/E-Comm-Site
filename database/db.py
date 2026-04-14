import sqlite3
import pandas as pd
import os
import hashlib

def hash_password(password):
    """Returns a SHA-256 hash of the given password string."""
    return hashlib.sha256(str(password).encode('utf-8')).hexdigest()

DB_PATH = 'database/ecommerce.db'

def get_connection():
    # Make sure the directory exists
    os.makedirs('database', exist_ok=True)
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_db():
    conn = get_connection()
    c = conn.cursor()
    
    # Create Users Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('customer', 'manager', 'administrator')),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create Products Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            price REAL NOT NULL,
            cost REAL NOT NULL,
            stock INTEGER NOT NULL,
            reorder_point INTEGER NOT NULL,
            lead_time_days INTEGER NOT NULL,
            rating REAL,
            description TEXT,
            image_url TEXT,
            is_active BOOLEAN DEFAULT 1
        )
    ''')
    
    # Create Sales Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS sales (
            order_id TEXT NOT NULL,
            product_id INTEGER NOT NULL,
            units_sold INTEGER NOT NULL,
            user_email TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(product_id) REFERENCES products(id)
        )
    ''')
    
    # Create Ratings Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS user_ratings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT NOT NULL,
            product_id INTEGER NOT NULL,
            rating INTEGER NOT NULL CHECK(rating >= 1 AND rating <= 5),
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(product_id) REFERENCES products(id),
            UNIQUE(user_email, product_id)
        )
    ''')
    
    conn.commit()
    conn.close()

def get_dataframe(query, params=()):
    conn = get_connection()
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

def execute_query(query, params=()):
    conn = get_connection()
    c = conn.cursor()
    c.execute(query, params)
    conn.commit()
    last_row_id = c.lastrowid
    conn.close()
    return last_row_id

def execute_many(query, params_list):
    conn = get_connection()
    c = conn.cursor()
    c.executemany(query, params_list)
    conn.commit()
    conn.close()
