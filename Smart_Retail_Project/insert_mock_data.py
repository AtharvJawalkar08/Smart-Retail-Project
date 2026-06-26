# ==========================================
# STEP 1: CONNECT TO OUR EXISTING DATABASE
# ==========================================
import sqlite3

# This connects to the database file we created in the last step
connection = sqlite3.connect("retail_store.db")
cursor = connection.cursor()

# ==========================================
# STEP 2: INSERT PRODUCTS INTO THE CATALOG
# ==========================================
# We use 'INSERT OR IGNORE' so the script doesn't crash if you run it multiple times.
# The numbers (101, 102, 103) are our manual product_id keys.
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
# Product 101: 50 in stock, alert us if it drops under 20.
# Product 102: 40 in stock, alert us if it drops under 15.
# Product 103: 100 in stock, alert us if it drops under 30.
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
# STEP 4: INSERT DAILY SALES TRANSACTIONS
# ==========================================
# This mimics sales over several days using the YYYY-MM-DD date format constraint.
# Format: (product_id, quantity_sold, sale_date)
sales_data = [
    (101, 5, '2026-06-01'),  # Milk sales
    (101, 7, '2026-06-02'),
    (101, 6, '2026-06-03'),
    (101, 12, '2026-06-04'), # Big sales spike!
    (101, 4, '2026-06-05'),
    
    (102, 3, '2026-06-01'),  # Bread sales
    (102, 4, '2026-06-02'),
    (102, 2, '2026-06-03'),
    (102, 5, '2026-06-04'),
    (102, 3, '2026-06-05'),
    
    (103, 15, '2026-06-01'), # Banana sales
    (103, 20, '2026-06-02'),
    (103, 18, '2026-06-03'),
    (103, 25, '2026-06-04'),
    (103, 12, '2026-06-05')
]

cursor.executemany("""
INSERT INTO sales_transactions (product_id, quantity_sold, sale_date)
VALUES (?, ?, ?);
""", sales_data)

# ==========================================
# STEP 5: SAVE AND CLOSE
# ==========================================
connection.commit()
connection.close()

print("Success! Mock store data has been safely injected.")
