# ==========================================
# STEP 1: CONNECT TO OUR EXISTING DATABASE
# ==========================================
import sqlite3
import numpy as np
from datetime import date, timedelta

connection = sqlite3.connect("retail_store.db")
cursor = connection.cursor()

# ==========================================
# STEP 2: INSERT PRODUCTS INTO THE CATALOG
# ==========================================
products_data = [
    (101, 'Organic Milk', 'Dairy', 3.99),
    (102, 'Whole Wheat Bread', 'Bakery', 2.49),
    (103, 'Fresh Bananas', 'Produce', 0.59)
]

cursor.executemany("""
INSERT OR IGNORE INTO products (product_id, product_name, category, price)
VALUES (?, ?, ?, ?);
""", products_data)

# ==========================================
# STEP 3: SET UP INITIAL INVENTORY LEVELS
# ==========================================
inventory_data = [
    (101, 50, 20),
    (102, 40, 15),
    (103, 100, 30)
]

cursor.executemany("""
INSERT OR IGNORE INTO inventory_levels (product_id, current_stock, minimum_required)
VALUES (?, ?, ?);
""", inventory_data)

# ==========================================
# STEP 4: GENERATE REALISTIC SALES HISTORY
# ==========================================
# Real demand forecasting needs enough history to detect weekly patterns.
# 5 days of hand-typed numbers can't show that. This generates 120 days
# (~17 weeks) per product, with:
#   - a base demand level per product
#   - a weekend spike (Sat/Sun sell more - typical grocery pattern)
#   - a mild upward trend (store is slowly growing)
#   - random day-to-day noise (real sales are never a perfect line)
#
# This is synthetic data - but it's synthetic with a known, realistic
# structure, which is what lets us prove the model can actually recover
# that structure later (see train_ai_model.py).

np.random.seed(42)  # reproducible: same "random" data every time this runs

# Clear old sales data so re-running this script doesn't just append more
cursor.execute("DELETE FROM sales_transactions;")

NUM_DAYS = 120
start_date = date(2026, 1, 1)

# (product_id, base_demand, weekend_multiplier, trend_per_day, noise_std)
product_profiles = [
    (101, 8,  1.6, 0.02, 1.5),   # Milk: steady staple, decent weekend bump
    (102, 4,  1.3, 0.01, 1.0),   # Bread: lower volume, smaller weekend bump
    (103, 18, 1.8, 0.05, 3.0),   # Bananas: high volume, big weekend bump, growing fast
]

sales_data = []
for product_id, base, weekend_mult, trend, noise_std in product_profiles:
    for day_offset in range(NUM_DAYS):
        current_date = start_date + timedelta(days=day_offset)
        weekday = current_date.weekday()  # 0=Mon ... 5=Sat, 6=Sun

        demand = base + (trend * day_offset)
        if weekday >= 5:  # weekend
            demand *= weekend_mult

        demand += np.random.normal(0, noise_std)
        quantity = max(0, round(demand))  # sales can't be negative

        sales_data.append((product_id, int(quantity), current_date.isoformat()))

cursor.executemany("""
INSERT INTO sales_transactions (product_id, quantity_sold, sale_date)
VALUES (?, ?, ?);
""", sales_data)

# ==========================================
# STEP 5: SAVE AND CLOSE
# ==========================================
connection.commit()
connection.close()

print(f"Success! Inserted {len(sales_data)} sales records "
      f"({NUM_DAYS} days x {len(product_profiles)} products).")
