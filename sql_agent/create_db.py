"""
Step 2a: Create a small sample sales database (SQLite) to test the SQL agent
against. Swap this out for your real company database later -- the agent
code doesn't change, only the connection string does.
"""

import sqlite3
import random
import os
from datetime import date, timedelta

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "sales.db")

PRODUCTS = [
    ("Laptop Pro", "Electronics", 1200),
    ("Wireless Mouse", "Electronics", 25),
    ("Office Chair", "Furniture", 180),
    ("Standing Desk", "Furniture", 350),
    ("Notebook Pack", "Stationery", 8),
    ("Pen Set", "Stationery", 12),
]

REGIONS = ["North", "South", "East", "West"]


def create_db():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE sales (
            sale_id INTEGER PRIMARY KEY,
            sale_date TEXT,
            product TEXT,
            category TEXT,
            region TEXT,
            quantity INTEGER,
            unit_price REAL,
            total_amount REAL
        )
    """)

    random.seed(42)
    start = date(2025, 1, 1)
    rows = []
    for i in range(1, 601):  # 600 sample sales rows across the year
        product, category, price = random.choice(PRODUCTS)
        d = start + timedelta(days=random.randint(0, 364))
        qty = random.randint(1, 8)
        region = random.choice(REGIONS)
        total = round(qty * price * random.uniform(0.9, 1.1), 2)  # slight price variation
        rows.append((i, d.isoformat(), product, category, region, qty, price, total))

    cur.executemany(
        "INSERT INTO sales VALUES (?, ?, ?, ?, ?, ?, ?, ?)", rows
    )
    conn.commit()
    conn.close()
    print(f"Created {DB_PATH} with {len(rows)} sample sales rows.")


if __name__ == "__main__":
    create_db()
