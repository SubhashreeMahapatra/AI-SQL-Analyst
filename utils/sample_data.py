import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
from datetime import datetime, timedelta
import random
import os


def initialize_sample_db():
    """Create an in-memory SQLite database with realistic e-commerce data."""
    engine = create_engine("sqlite:///./sample_ecommerce.db", echo=False)

    rng = np.random.default_rng(42)

    # ── Categories ────────────────────────────────────────────────────────────
    categories = pd.DataFrame({
        "id": range(1, 7),
        "name": ["Electronics", "Clothing", "Books", "Home & Garden", "Sports", "Beauty"],
    })

    # ── Products ──────────────────────────────────────────────────────────────
    product_names = {
        1: ["Laptop Pro X", "Wireless Earbuds", "Smart Watch", "USB-C Hub", "Webcam HD", "Mechanical Keyboard", "Monitor 27\"", "SSD 1TB"],
        2: ["Running Jacket", "Yoga Pants", "Cotton T-Shirt", "Winter Coat", "Sports Bra", "Denim Jeans", "Hoodie Classic", "Sneakers"],
        3: ["Python Mastery", "Data Science 101", "The Art of SQL", "Clean Code", "AI for Everyone", "System Design", "Node.js Cookbook"],
        4: ["Indoor Plant Set", "LED Strip Light", "Air Purifier", "Coffee Maker Pro", "Desk Organizer", "Scented Candles"],
        5: ["Yoga Mat", "Resistance Bands", "Foam Roller", "Jump Rope", "Dumbbells 10kg", "Pull-up Bar", "Cycling Gloves"],
        6: ["Vitamin C Serum", "Moisturizer SPF50", "Shampoo Pro", "Face Mask Set", "Lip Care Kit", "Eye Cream"],
    }
    products = []
    pid = 1
    for cat_id, names in product_names.items():
        for name in names:
            base_price = rng.uniform(10, 500)
            products.append({
                "id": pid,
                "name": name,
                "category_id": cat_id,
                "price": round(float(base_price), 2),
                "cost": round(float(base_price * rng.uniform(0.3, 0.6)), 2),
                "stock_quantity": int(rng.integers(0, 500)),
            })
            pid += 1
    products_df = pd.DataFrame(products)

    # ── Customers ─────────────────────────────────────────────────────────────
    regions = ["North America", "Europe", "Asia Pacific", "Latin America", "Middle East"]
    first_names = ["Alice", "Bob", "Carlos", "Diana", "Emma", "Fiona", "George", "Hannah",
                   "Ivan", "Julia", "Kevin", "Laura", "Mike", "Nina", "Oscar", "Priya",
                   "Quinn", "Rachel", "Sam", "Tara", "Umar", "Vera", "Will", "Xia", "Yuki", "Zoe"]
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Miller", "Davis",
                  "Garcia", "Rodriguez", "Wilson", "Martinez", "Anderson", "Taylor", "Thomas"]

    n_customers = 500
    customers = pd.DataFrame({
        "id": range(1, n_customers + 1),
        "first_name": rng.choice(first_names, n_customers),
        "last_name": rng.choice(last_names, n_customers),
        "email": [f"user{i}@example.com" for i in range(1, n_customers + 1)],
        "region": rng.choice(regions, n_customers),
        "signup_date": pd.to_datetime("2022-01-01") + pd.to_timedelta(rng.integers(0, 730, n_customers), unit="D"),
        "lifetime_value": rng.uniform(50, 5000, n_customers).round(2),
    })

    # ── Orders ────────────────────────────────────────────────────────────────
    statuses = ["completed", "completed", "completed", "shipped", "pending", "refunded"]
    n_orders = 3000
    start = datetime(2023, 1, 1)

    # Add Q4 boost
    def random_date():
        day = int(rng.integers(0, 365))
        d = start + timedelta(days=day)
        # Boost Q4 (Oct-Dec) frequency
        if rng.random() < 0.35:
            d = datetime(2023, 10, 1) + timedelta(days=int(rng.integers(0, 92)))
        return d

    order_dates = [random_date() for _ in range(n_orders)]
    customer_ids = rng.choice(range(1, n_customers + 1), n_orders)

    orders = pd.DataFrame({
        "id": range(1, n_orders + 1),
        "customer_id": customer_ids,
        "order_date": order_dates,
        "status": rng.choice(statuses, n_orders),
        "region": [customers.loc[c - 1, "region"] for c in customer_ids],
        "shipping_cost": rng.uniform(0, 20, n_orders).round(2),
        "discount_pct": rng.choice([0, 0, 0, 5, 10, 15, 20], n_orders),
    })

    # ── Order Items ───────────────────────────────────────────────────────────
    order_items = []
    oi_id = 1
    for order_id in range(1, n_orders + 1):
        n_items = int(rng.integers(1, 5))
        selected_products = rng.choice(range(len(products_df)), n_items, replace=False)
        for pi in selected_products:
            product = products_df.iloc[pi]
            qty = int(rng.integers(1, 5))
            price = float(product["price"])
            order_items.append({
                "id": oi_id,
                "order_id": order_id,
                "product_id": int(product["id"]),
                "quantity": qty,
                "unit_price": price,
                "total_price": round(price * qty, 2),
            })
            oi_id += 1
    order_items_df = pd.DataFrame(order_items)

    # Update orders with total amount
    totals = order_items_df.groupby("order_id")["total_price"].sum().reset_index()
    totals.columns = ["id", "total_amount"]
    orders = orders.merge(totals, on="id", how="left")
    orders["total_amount"] = orders["total_amount"].round(2)

    # ── Write to DB ───────────────────────────────────────────────────────────
    categories.to_sql("categories", engine, if_exists="replace", index=False)
    products_df.to_sql("products", engine, if_exists="replace", index=False)
    customers.to_sql("customers", engine, if_exists="replace", index=False)
    orders.to_sql("orders", engine, if_exists="replace", index=False)
    order_items_df.to_sql("order_items", engine, if_exists="replace", index=False)

    # ── Convenience View ──────────────────────────────────────────────────────
    with engine.connect() as conn:
        conn.execute(text("""
        CREATE VIEW IF NOT EXISTS sales_summary AS
        SELECT
            o.id AS order_id,
            o.order_date,
            strftime('%Y', o.order_date) AS year,
            strftime('%m', o.order_date) AS month,
            CASE
                WHEN CAST(strftime('%m', o.order_date) AS INTEGER) BETWEEN 1 AND 3 THEN 'Q1'
                WHEN CAST(strftime('%m', o.order_date) AS INTEGER) BETWEEN 4 AND 6 THEN 'Q2'
                WHEN CAST(strftime('%m', o.order_date) AS INTEGER) BETWEEN 7 AND 9 THEN 'Q3'
                ELSE 'Q4'
            END AS quarter,
            o.region,
            o.status,
            o.total_amount,
            c.first_name || ' ' || c.last_name AS customer_name,
            c.region AS customer_region,
            p.name AS product_name,
            cat.name AS category_name,
            oi.quantity,
            oi.unit_price,
            oi.total_price AS item_total
        FROM orders o
        JOIN customers c ON o.customer_id = c.id
        JOIN order_items oi ON o.id = oi.order_id
        JOIN products p ON oi.product_id = p.id
        JOIN categories cat ON p.category_id = cat.id
        WHERE o.status = 'completed'
        """))
        conn.commit()

    return engine
