# ==========================================
# STEP 1: LOAD STREAMLIT AND DATABASE ENGINES
# ==========================================
import streamlit as st
import sqlite3
import pandas as pd
import joblib
from datetime import timedelta

# Set up the title page header configuration
st.set_page_config(page_title="Predictive Inventory System", layout="centered")
st.title("🛍️ Smart Retail Restocking Dashboard")
st.write("Welcome, Manager! Below are your AI-driven product restocking thresholds.")

# ==========================================
# STEP 2: FETCH LIVE SQL DATABASE INFORMATION
# ==========================================
connection = sqlite3.connect("retail_store.db")

query_stock = """
SELECT p.product_id, p.product_name, p.category, i.current_stock, i.minimum_required
FROM products p
JOIN inventory_levels i ON p.product_id = i.product_id;
"""
df_stock = pd.read_sql_query(query_stock, connection)

query_sales = "SELECT product_id, quantity_sold, sale_date FROM sales_transactions;"
df_sales = pd.read_sql_query(query_sales, connection)

connection.close()

# ==========================================
# STEP 3: LOAD PRE-TRAINED PER-PRODUCT MODELS
# ==========================================
# Models are trained once offline (train_ai_model.py) with a proper
# train/test split and evaluated against a naive baseline, then saved.
# The app just loads and uses them - it does not retrain on every click.
@st.cache_resource
def load_demand_models():
    return joblib.load("models/demand_models.joblib")

demand_data = load_demand_models()
models = demand_data["models"]
metrics = demand_data["metrics"]

# ==========================================
# STEP 4: CREATING USER SELECTION DROPDOWNS
# ==========================================
selected_product_name = st.selectbox("Select an item to inspect:", df_stock['product_name'].unique())

product_row = df_stock[df_stock['product_name'] == selected_product_name].iloc[0]
product_id = int(product_row['product_id'])
current_stock = int(product_row['current_stock'])
min_required = int(product_row['minimum_required'])

# ==========================================
# STEP 5: PREDICT NEXT WEEK'S DEMAND WITH THE SAVED MODEL
# ==========================================
df_item_sales = df_sales[df_sales['product_id'] == product_id].copy()

if product_id in models and not df_item_sales.empty:
    model = models[product_id]
    product_metrics = metrics[product_id]

    df_item_sales['sale_date'] = pd.to_datetime(df_item_sales['sale_date'])
    last_date = df_item_sales['sale_date'].max()
    last_day_number = product_metrics["last_day_number"]

    # Predict 7 days ahead, using the correct day-of-week for that future date
    # (this is the seasonality feature the original model didn't have)
    target_date = last_date + timedelta(days=7)
    next_week_frame = pd.DataFrame({
        'day_number': [last_day_number + 7],
        'day_of_week': [target_date.dayofweek],
    })
    prediction = int(round(model.predict(next_week_frame)[0]))

    model_mae = product_metrics["model_mae"]
    baseline_mae = product_metrics["naive_baseline_mae"]
else:
    prediction = 0
    model_mae = None
    baseline_mae = None

# ==========================================
# STEP 6: DISPLAY METRIC SCORES ON DASHBOARD
# ==========================================
col1, col2, col3 = st.columns(3)
col1.metric("Current Stock", f"{current_stock} units")
col2.metric("Safety Buffer", f"{min_required} units")
col3.metric("AI Predicted Next Week Demand", f"{prediction} units")

if model_mae is not None:
    beats_text = "beats" if model_mae < baseline_mae else "does not beat"
    st.caption(
        f"Model test MAE: {model_mae} units/day vs. {baseline_mae} units/day for a "
        f"naive 'same as yesterday' baseline — model {beats_text} the baseline "
        f"on held-out data."
    )

# ==========================================
# STEP 6.5: VISUAL STOCK LEVEL PROGRESS BAR
# ==========================================
st.markdown(" ")
st.subheader("📊 Shelf Capacity Analyzer")

fill_percentage = min(current_stock / (min_required * 2), 1.0)

if current_stock < min_required:
    st.error(f"🔴 Stock is dangerously low! Current level is at {int(fill_percentage * 100)}% of recommended maximum capacity.")
    st.progress(fill_percentage)
elif current_stock < (min_required * 1.5):
    st.warning(f"🟡 Stock is adequate but dwindling. Current level is at {int(fill_percentage * 100)}% capacity.")
    st.progress(fill_percentage)
else:
    st.success(f"🟢 Stock levels are secure! Shelves are sitting comfortably at {int(fill_percentage * 100)}% capacity.")
    st.progress(fill_percentage)

# ==========================================
# STEP 7: BUSINESS RESTOCK LOGIC CHECKS
# ==========================================
st.markdown("---")
st.subheader("📋 Automated Ordering Recommendation")

predicted_deficit = current_stock - prediction

if current_stock < min_required:
    st.error(f"🚨 CRITICAL ALERT: Item is currently below safety levels! Order immediate replacement stocks.")
elif predicted_deficit < min_required:
    order_amount = (min_required + prediction) - current_stock
    st.warning(f"⚠️ RESTOCK ADVISORY: Upcoming weekly forecast demands will trigger shortage. Order **{order_amount} units** now.")
else:
    st.success("✅ OPTIMAL INVENTORY: Shelves look fully optimized. No orders necessary today.")

# ==========================================
# STEP 8: ADD A VISUAL DEMAND GRAPH ON SCREEN
# ==========================================
st.markdown("---")
st.subheader("📊 Historical Sales & Demand Trajectory")

if not df_item_sales.empty:
    df_plot = df_item_sales.sort_values('sale_date')
    chart_data = df_plot.set_index('sale_date')[['quantity_sold']]
    st.line_chart(chart_data)
else:
    st.info("No transaction tracking data points found for this item yet.")

# ==========================================
# STEP 9: SIMULATE AN INVENTORY RESTOCK
# ==========================================
st.markdown("---")
st.subheader("📦 Order Fulfillment Simulation")
st.write("Simulate receiving a supplier shipment to top up inventory levels back into your SQL warehouse.")

if st.button("📥 Receive +50 Units Stock Delivery"):
    write_conn = sqlite3.connect("retail_store.db")
    write_cursor = write_conn.cursor()
    write_cursor.execute("""
        UPDATE inventory_levels
        SET current_stock = current_stock + 50
        WHERE product_id = ?;
    """, (product_id,))
    write_conn.commit()
    write_conn.close()

    st.success(f"Successfully processed supplier shipment! +50 units added to {selected_product_name}.")
    st.rerun()
