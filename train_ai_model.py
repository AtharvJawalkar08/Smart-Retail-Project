# ==========================================
# STEP 1: IMPORT TOOLS
# ==========================================
import sqlite3
import pandas as pd
import numpy as np
import joblib
from pathlib import Path
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error

# ==========================================
# STEP 2: LOAD ALL SALES DATA
# ==========================================
connection = sqlite3.connect("retail_store.db")
query = "SELECT product_id, quantity_sold, sale_date FROM sales_transactions;"
df = pd.read_sql_query(query, connection)
connection.close()

df['sale_date'] = pd.to_datetime(df['sale_date'])

# ==========================================
# STEP 3: TRAIN ONE MODEL PER PRODUCT
# ==========================================
# Fixing the original bug: this loops per product_id instead of pooling
# everything into one regression. Milk, bread, and bananas each get
# their own model, because they have different demand patterns.
#
# Each model uses two features:
#   - day_number: captures the overall trend (growing/shrinking demand)
#   - day_of_week: captures weekly seasonality (weekend spikes)
#
# We split chronologically (train on the first 80% of days, test on the
# most recent 20%) rather than randomly, because that's how forecasting
# actually gets used: predict the future from the past, never the reverse.

models = {}
metrics = {}

for product_id in sorted(df['product_id'].unique()):
    product_df = df[df['product_id'] == product_id].sort_values('sale_date').copy()
    product_df['day_number'] = (
        product_df['sale_date'] - product_df['sale_date'].min()
    ).dt.days + 1
    product_df['day_of_week'] = product_df['sale_date'].dt.dayofweek  # 0=Mon..6=Sun

    X = product_df[['day_number', 'day_of_week']]
    y = product_df['quantity_sold']

    split_idx = int(len(product_df) * 0.8)
    X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
    y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]

    model = LinearRegression()
    model.fit(X_train, y_train)

    preds = model.predict(X_test)
    mae = mean_absolute_error(y_test, preds)

    # Baseline: "predict tomorrow = same as today" (naive persistence baseline)
    # This is the standard, honest baseline for time series - if your model
    # can't beat "just guess yesterday's number," it isn't earning its keep.
    naive_preds = y_test.shift(1).bfill()
    naive_mae = mean_absolute_error(y_test, naive_preds)

    models[product_id] = model
    metrics[product_id] = {
        "model_mae": round(mae, 2),
        "naive_baseline_mae": round(naive_mae, 2),
        "n_train_days": len(X_train),
        "n_test_days": len(X_test),
        "last_day_number": int(product_df['day_number'].max()),
    }

    print(f"Product {product_id}: model MAE = {mae:.2f}, "
          f"naive baseline MAE = {naive_mae:.2f} "
          f"({'beats' if mae < naive_mae else 'does NOT beat'} baseline)")

# ==========================================
# STEP 4: SAVE MODELS + METRICS TOGETHER
# ==========================================
# app.py loads this file instead of retraining live on every click.
# Retraining a linear model on 100 rows is fast, but saving once and
# loading is the correct pattern for anything that scales past a toy demo.
Path("models").mkdir(exist_ok=True)
joblib.dump({"models": models, "metrics": metrics}, "models/demand_models.joblib")

print("\nSaved all per-product models and metrics to models/demand_models.joblib")
