import random
import uuid
import datetime
import os
from database.db import init_db, execute_many, execute_query, get_connection, hash_password

CATEGORIES = [
    {"name": "Laptops", "base_price": 800, "keywords": ["portable", "work", "school", "gaming", "fast"]},
    {"name": "Smartphones", "base_price": 500, "keywords": ["mobile", "camera", "battery", "calls", "apps"]},
    {"name": "Headphones", "base_price": 50, "keywords": ["audio", "bass", "noise-canceling", "wireless", "music"]},
    {"name": "Monitors", "base_price": 150, "keywords": ["display", "screen", "4k", "refresh rate", "office"]},
    {"name": "Keyboards", "base_price": 30, "keywords": ["typing", "mechanical", "wireless", "ergonomic", "RGB"]}
]

ADJECTIVES = ["Premium", "Ultra", "Smart", "Pro", "Elite", "Compact", "Advanced", "Basic"]

def generate_products(n=50):
    products = []
    for _ in range(n):
        cat = random.choice(CATEGORIES)
        adj = random.choice(ADJECTIVES)
        name = f"{adj} {cat['name'][:-1]} Model {random.randint(10, 99)}"
        price = round(cat['base_price'] * random.uniform(0.8, 1.5), 2)
        cost = round(price * random.uniform(0.4, 0.7), 2) # Profit margin 30-60%
        stock = random.randint(10, 200)
        reorder_point = random.randint(15, 50)
        lead_time_days = random.randint(2, 14)
        rating = round(random.uniform(3.5, 5.0), 1)
        
        # Build a description using keywords
        kws = random.sample(cat['keywords'], k=min(3, len(cat['keywords'])))
        desc = f"A {adj.lower()} {cat['name'][:-1].lower()} perfect for {', '.join(kws)}. Features high quality build and excellent performance. Upgrade your setup today."
        
        # Map to local high-quality AI generated assets
        asset_map = {
            "Laptops": "assets/laptop.png",
            "Smartphones": "assets/smartphone.png",
            "Headphones": "assets/headphones.png",
            "Monitors": "assets/monitor.png",
            "Keyboards": "assets/keyboard.png"
        }
        image_url = asset_map.get(cat['name'], "assets/laptop.png")
        
        products.append((name, cat['name'], price, cost, stock, reorder_point, lead_time_days, rating, desc, image_url))
    
    query = '''
        INSERT INTO products (name, category, price, cost, stock, reorder_point, lead_time_days, rating, description, image_url)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    '''
    execute_many(query, products)
    print(f"Inserted {n} products.")

def generate_users():
    users = [
        ("admin@example.com", hash_password("admin123"), "administrator"),
        ("manager@example.com", hash_password("manager123"), "manager")
    ]
    # Add 20 customers
    for i in range(1, 21):
        users.append((f"user{i}@example.com", hash_password("password123"), "customer"))
        
    query = "INSERT INTO users (email, password, role) VALUES (?, ?, ?)"
    execute_many(query, users)
    print(f"Inserted {len(users)} users.")

def generate_sales_and_ratings(num_orders=200):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id, rating FROM products")
    products = c.fetchall()
    conn.close()
    
    if not products:
        print("No products found.")
        return

    # Fetch users
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT email FROM users WHERE role = 'customer'")
    customer_emails = [row[0] for row in c.fetchall()]
    conn.close()
    
    sales_data = []
    ratings_data = []
    
    # Track existing ratings to avoid duplicates (user_email, product_id)
    rating_pairs = set()

    for _ in range(num_orders):
        order_id = str(uuid.uuid4())[:8]
        user_email = random.choice(customer_emails)
        
        # Market basket simulation: 1-4 items per order
        num_items = random.choices([1, 2, 3, 4], weights=[0.5, 0.3, 0.15, 0.05])[0]
        
        # Frequently bought together logic could be injected here, but random is fine for mock
        chosen_products = random.sample(products, k=min(num_items, len(products)))
        
        # Order date within last 60 days
        days_ago = random.randint(0, 60)
        timestamp = datetime.datetime.now() - datetime.timedelta(days=days_ago)
        
        for p in chosen_products:
            p_id = p[0]
            units = random.randint(1, 3)
            sales_data.append((order_id, p_id, units, user_email, timestamp.strftime("%Y-%m-%d %H:%M:%S")))
            
            # 30% chance user leaves a rating
            if random.random() < 0.3:
                pair = (user_email, p_id)
                if pair not in rating_pairs:
                    rating_pairs.add(pair)
                    # Rating slightly guided by product's base rating
                    base_rating = p[1]
                    user_rating = min(5, max(1, int(round(random.gauss(base_rating, 0.8)))))
                    ratings_data.append((user_email, p_id, user_rating, timestamp.strftime("%Y-%m-%d %H:%M:%S")))

    s_query = '''
        INSERT INTO sales (order_id, product_id, units_sold, user_email, timestamp)
        VALUES (?, ?, ?, ?, ?)
    '''
    execute_many(s_query, sales_data)
    print(f"Inserted {len(sales_data)} sales records.")
    
    if ratings_data:
        r_query = '''
            INSERT INTO user_ratings (user_email, product_id, rating, timestamp)
            VALUES (?, ?, ?, ?)
        '''
        execute_many(r_query, ratings_data)
        print(f"Inserted {len(ratings_data)} ratings.")

def build_mock_data():
    if os.path.exists('database/ecommerce.db'):
        os.remove('database/ecommerce.db')
    
    init_db()
    generate_users()
    generate_products(60)
    generate_sales_and_ratings(300)

if __name__ == '__main__':
    build_mock_data()
