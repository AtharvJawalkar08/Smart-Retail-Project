# ==========================================
# STEP 1: IMPORT THE DATABASE ENGINE
# ==========================================
# Python has a built-in database system called 'sqlite3'. 
# This line tells Python to load it up so we can use its tools.
import sqlite3

# ==========================================
# STEP 2: CREATE AND CONNECT TO THE DATABASE
# ==========================================
# This line tells Python to look for a file called 'retail_store.db'.
# If it does not find it, Python will automatically create a brand new file with that name right inside your folder.
connection = sqlite3.connect("retail_store.db")

# ==========================================
# STEP 3: CREATE A DIGITAL POINTER (CURSOR)
# ==========================================
# Think of the cursor as a pen. We use it to type out instructions and execute commands inside the database.
cursor = connection.cursor()

# ==========================================
# STEP 4: CREATE THE PRODUCTS TABLE
# ==========================================
# This command tells the database to build a structured table named 'products'.
# 'IF NOT EXISTS' stops the code from crashing if you accidentally run this file twice.
cursor.execute("""
CREATE TABLE IF NOT EXISTS products (
    product_id INTEGER PRIMARY KEY,   -- Every product gets a unique ID number that cannot be shared
    product_name TEXT NOT NULL,       -- Stores text names like 'Apples'. 'NOT NULL' means it cannot be blank
    category TEXT NOT NULL,           -- Stores group names like 'Produce' or 'Dairy'
    price REAL NOT NULL               -- Stores decimal numbers for pricing data
);
""")

# ==========================================
# STEP 5: CREATE THE SALES TRANSACTIONS TABLE
# ==========================================
# This builds our sales tracking sheet.
cursor.execute("""
CREATE TABLE IF NOT EXISTS sales_transactions (
    transaction_id INTEGER PRIMARY KEY AUTOINCREMENT, -- Automatically counts receipts (1, 2, 3...) so you don't have to
    product_id INTEGER,                               -- Tells us exactly which item from the catalog was sold
    quantity_sold INTEGER NOT NULL,                   -- Holds a whole number of items bought
    sale_date TEXT NOT NULL,                          -- Stores the calendar date (Must always be YYYY-MM-DD)
    FOREIGN KEY (product_id) REFERENCES products (product_id) -- Data safety rope: stops us from selling a fake product ID
);
""")

# ==========================================
# STEP 6: CREATE THE INVENTORY STOCK TABLE
# ==========================================
# This builds our warehouse shelf tracking sheet.
cursor.execute("""
CREATE TABLE IF NOT EXISTS inventory_levels (
    product_id INTEGER PRIMARY KEY,          -- Links directly to the master product list
    current_stock INTEGER NOT NULL,          -- How many units are sitting on the physical shelf right now
    minimum_required INTEGER NOT NULL,       -- The alert buffer. If stock goes under this, we need to order more
    FOREIGN KEY (product_id) REFERENCES products (product_id)
);
""")

# ==========================================
# STEP 7: SAVE ALL WORK AND CLOSE
# ==========================================
# Databases do not auto-save. 'commit()' pushes a physical save button to write your tables safely to the file.
connection.commit()

# This safely detaches the database from your computer's memory so your file doesn't get locked up or corrupted.
connection.close()

print("Success! Your database file 'retail_store.db' and tables are built.")
