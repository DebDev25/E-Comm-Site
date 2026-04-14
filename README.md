# E-Comm-Site

A comprehensive, AI-driven E-Commerce and Strategic Operations platform built with **Streamlit**. This application integrates advanced machine learning for product recommendations, semantic search, and inventory forecasting to provide a modern retail experience for customers, managers, and administrators.

## 🚀 Key Features

### 🛒 Customer Storefront
- **NLP Semantic Search**: Describe what you need in natural language, and our AI finds the most relevant products using TF-IDF vectorization.
- **Personalized Recommendations**: User-to-Item Collaborative Filtering suggests products based on shopping history and similarities to other users.
- **Smart Catalog**: Dynamic product grid with category filtering and real-time stock status.
- **AI-Powered Product Details**:
    - **Similar Items**: Content-based filtering to find products with similar features.
    - **Market Basket Analysis**: "Frequently Bought Together" recommendations based on historical co-occurrence in orders.

### 📈 Manager Dashboard
- **Strategic Metrics**: Real-time tracking of Total Revenue, Profit, and Margins.
- **Performance Analytics**: Visualizations for revenue by category and daily sales velocity.
- **AI Inventory Forecasting**: Predictive modeling (Random Forest) to estimate 30-day demand and flag critical reorder points before stockouts occur.
- **Catalog Management**: Full CRUD operations to manage product listings, pricing, and stock levels.

### 🛡️ Admin Panel
- **Role-Based Access Control (RBAC)**: Secure access for Customers, Managers, and Administrators.
- **User Management**: Interface to add new staff, reset credentials, and modify access roles.

## 🛠️ Technology Stack
- **Frontend**: [Streamlit](https://streamlit.io/)
- **Data & Analytics**: [Pandas](https://pandas.pydata.org/), [NumPy](https://numpy.org/)
- **Machine Learning**: [Scikit-Learn](https://scikit-learn.org/) (Random Forest, TF-IDF, Cosine Similarity)
- **Visualizations**: [Altair](https://altair-viz.github.io/)
- **Database**: SQLite3 (Local, lightweight, and performant)
- **Styling**: Vanilla CSS (Modern, premium glassmorphism aesthetic)

## 📁 Project Structure
```text
Ecommerce Site/
├── app.py              # Main entry point & Authentication
├── requirements.txt    # Project dependencies
├── database/           # DB Utilities & Mock Data Generator
├── pages/              # Multi-page application structure
├── ml/                 # Machine Learning models (Search, Recs, Forecast)
├── styles/             # Custom CSS styling
└── assets/             # Product images and UI assets
```

## ⚙️ Installation & Setup

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd "Ecommerce Site"
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**:
   ```bash
   streamlit run app.py
   ```

4. **Initial Setup**:
   - On first run, the system will automatically bootstrap a SQLite database (`database/ecommerce.db`) with generated mock products, users, and sales history.
   - **Default Credentials**:
     - **Admin**: `admin@example.com` / `admin123`
     - **Manager**: `manager@example.com` / `manager123`
     - **Customer**: `user1@example.com` / `password123`

## 🧠 Model Details
- **Search & Similarity**: Uses `TfidfVectorizer` to convert product text into numerical space, allowing for high-performance cosine similarity comparisons.
- **Demand Forecasting**: Uses a `RandomForestRegressor` trained on historical sales velocity, pricing, and product ratings to predict future stock requirements.

## 🎨 Aesthetic Design
The platform features a custom design system defined in `styles/main.css`, focusing on:
- **Glassmorphism**: Translucent UI components for a modern look.
- **Dynamic Cards**: Hover effects and status badges for intuitive navigation.
- **Responsive Layouts**: Optimized for various screen sizes.

