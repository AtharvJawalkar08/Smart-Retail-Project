# ==========================================
# STEP 1: LOAD STREAMLIT AND DATABASE ENGINES
# ==========================================
import streamlit as st
import sqlite3
import pandas as pd
from sklearn.linear_model import LinearRegression

# Set up the title page header configuration
st.set_page_config(page_title="Predictive Inventory System", layout="centered")
st.title("🛍️ Smart Retail Restocking Dashboard")
st.write("Welcome, Manager! Below are your AI-driven product restocking thresholds.")

# ==========================================
# STEP 2: FETCH LIVE SQL DATABASE INFORMATION
# ==========================================
connection = sqlite3.connect("retail_store.db")

# Query 1: Get products with their names and stockroom status
query_stock = """
SELECT p.product_id, p.product_name, p.category, i.current_stock, i.minimum_required
FROM products p
JOIN inventory_levels i ON p.product_id = i.product_id;
"""
df_stock = pd.read_sql_query(query_stock, connection)

# Query 2: Get transaction history for predictive model processing
query_sales = "SELECT product_id, quantity_sold, sale_date FROM sales_transactions;"
df_sales = pd.read_sql_query(query_sales, connection)

connection.close()

# ==========================================
# STEP 3: CREATING USER SELECTION DROPDOWNS
# ==========================================
# Allow the manager to click a dropdown menu to select a product name from the database
selected_product_name = st.selectbox("Select an item to inspect:", df_stock['product_name'].unique())

# Extract specific database row matching user choice
product_row = df_stock[df_stock['product_name'] == selected_product_name].iloc[0]
product_id = int(product_row['product_id'])
current_stock = int(product_row['current_stock'])
min_required = int(product_row['minimum_required'])

# ==========================================
# STEP 4: TRAIN AI LIVE FOR CHOSEN ITEM
# ==========================================
# Filter history table down to only show records for the user's selected product ID
df_item_sales = df_sales[df_sales['product_id'] == product_id].copy()

# Guard block: If product has historical records, compute trend curve line
if not df_item_sales.empty:
    df_item_sales['sale_date'] = pd.to_datetime(df_item_sales['sale_date'])
    df_item_sales['day_number'] = (df_item_sales['sale_date'] - df_item_sales['sale_date'].min()).dt.days + 1
    
    # Train localized predictor engine
    X = df_item_sales[['day_number']]
    y = df_item_sales['quantity_sold']
    model = LinearRegression().fit(X, y)
    
    # Run a prediction for next week's counter interval (Day 8)
    next_week_frame = pd.DataFrame({'day_number': [8]})
    prediction = int(round(model.predict(next_week_frame)[0]))
else:
    prediction = 0 # Default safety fallback counter if item never sold yet

# ==========================================
# STEP 5: DISPLAY METRIC SCORES ON DASHBOARD
# ==========================================
# Render beautiful tracking cards across columns
col1, col2, col3 = st.columns(3)
col1.metric("Current Stock", f"{current_stock} units")
col2.metric("Safety Buffer", f"{min_required} units")
col3.metric("AI Predicted Next Week Demand", f"{prediction} units")
# ==========================================
# STEP 5.5: VISUAL STOCK LEVEL PROGRESS BAR
# ==========================================
st.markdown(" ") # Adds a small breathing room space on the page
st.subheader("📊 Shelf Capacity Analyzer")

# Calculate the current fill percentage of the item shelf
# We cap the percentage scale at 1.0 (100%) so the bar doesn't overflow
fill_percentage = min(current_stock / (min_required * 2), 1.0)

# Business Logic: Determine the structural health color of our stockroom
if current_stock < min_required:
    # Critical state: Show text warning notice
    st.error(f"🔴 Stock is dangerously low! Current level is at {int(fill_percentage * 100)}% of recommended maximum capacity.")
    st.progress(fill_percentage)
elif current_stock < (min_required * 1.5):
    # Warning state: Approaching danger zone threshold levels
    st.warning(f"🟡 Stock is adequate but dwindling. Current level is at {int(fill_percentage * 100)}% capacity.")
    st.progress(fill_percentage)
else:
    # Healthy state: Fully stocked shelves
    st.success(f"🟢 Stock levels are secure! Shelves are sitting comfortably at {int(fill_percentage * 100)}% capacity.")
    st.progress(fill_percentage)

# ==========================================
# STEP 6: BUSINESS RESTOCK LOGIC CHECKS
# ==========================================
st.markdown("---")
st.subheader("📋 Automated Ordering Recommendation")

# If current inventory cannot meet expected sales plus safety net margin, order stock
predicted_deficit = current_stock - prediction

if current_stock < min_required:
    st.error(f"🚨 CRITICAL ALERT: Item is currently below safety levels! Order immediate replacement stocks.")
elif predicted_deficit < min_required:
    order_amount = (min_required + prediction) - current_stock
    st.warning(f"⚠️ RESTOCK ADVISORY: Upcoming weekly forecast demands will trigger shortage. Order **{order_amount} units** now.")
else:
    st.success("✅ OPTIMAL INVENTORY: Shelves look fully optimized. No orders necessary today.")
# ==========================================
# STEP 7: ADD A VISUAL DEMAND GRAPH ON SCREEN
# ==========================================
st.markdown("---")
st.subheader("📊 Historical Sales & Demand Trajectory")

# Check if the chosen product has past sales history to plot
if not df_item_sales.empty:
    # Sort chronological transactions by order date
    df_plot = df_item_sales.sort_values('sale_date')
    
    # We create a simple line chart where:
    # index = the dates on the bottom horizontal axis
    # columns = the quantity sold on the vertical axis
    chart_data = df_plot.set_index('sale_date')[['quantity_sold']]
    
    # Streamlit has a built-in native line chart feature! One line of code builds a graph.
    st.line_chart(chart_data)
else:
    st.info("No transaction tracking data points found for this item yet.")
# ==========================================
# STEP 8: SIMULATE AN INVENTORY RESTOCK
# ==========================================
st.markdown("---")
st.subheader("📦 Order Fulfillment Simulation")
st.write("Simulate receiving a supplier shipment to top up inventory levels back into your SQL warehouse.")

# Create an interactive clickable action button on screen
if st.button("📥 Receive +50 Units Stock Delivery"):
    
    # Open a live write-connection into our local database
    write_conn = sqlite3.connect("retail_store.db")
    write_cursor = write_conn.cursor()
    
    # Execute a SQL command to update the stock level for our selected item
    write_cursor.execute("""
        UPDATE inventory_levels 
        SET current_stock = current_stock + 50 
        WHERE product_id = ?;
    """, (product_id,))
    
    # Save the change permanently inside our SQL files
    write_conn.commit()
    write_conn.close()
    
    # Display a green success popup message and force the web page to reload fresh numbers!
    st.success(f"Successfully processed supplier shipment! +50 units added to {selected_product_name}.")
    st.rerun()
