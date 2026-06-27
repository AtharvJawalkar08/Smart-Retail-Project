# ==========================================
# STEP 1: IMPORT OUR AI ENGINE AND TOOLS
# ==========================================
import sqlite3
import pandas as pd
# 'LinearRegression' is the mathematical AI model that draws a best-fit line through data points
from sklearn.linear_model import LinearRegression

# ==========================================
# STEP 2: LOAD DATA DIRECTLY FROM THE SQL FILES
# ==========================================
connection = sqlite3.connect("retail_store.db")

# We grab the item sales transactions history table
query = "SELECT product_id, quantity_sold, sale_date FROM sales_transactions;"
df = pd.read_sql_query(query, connection)
connection.close()

# ==========================================
# STEP 3: PREPARE THE DATA FOR MACHINE LEARNING
# ==========================================
# Machine learning algorithms can't read text calendar dates like '2026-06-01'. 
# They need simple numerical counts. Let's convert our dates into a day number counter (Day 1, Day 2, Day 3...)
df['sale_date'] = pd.to_datetime(df['sale_date'])
df['day_number'] = (df['sale_date'] - df['sale_date'].min()).dt.days + 1

# ==========================================
# STEP 4: SEPARATE DATA INTO FEATURES AND TARGETS
# ==========================================
# X (Features) = What information the AI looks at to make a guess (The Day Number)
# y (Target) = The final answer we want our AI to predict (The Quantity Sold)
X = df[['day_number']]
y = df['quantity_sold']

# ==========================================
# STEP 5: TRAIN THE PREDICTIVE AI MODEL
# ==========================================
# We initialize the blank AI algorithm container
model = LinearRegression()

# '.fit()' is the magic button. It forces the AI to look at the patterns between X and y and learn the trend.
model.fit(X, y)

print("--- AI Model Successfully Trained ---")

# ==========================================
# STEP 6: PREDICT NEXT WEEK'S DEMAND (DAY 8)
# ==========================================
# Our mock data went up to Day 5. Let's ask the AI to predict what will sell on Day 8 (Next Week).
next_week_day = pd.DataFrame({'day_number': [8]})
predicted_sales = model.predict(next_week_day)

# Print out the results rounded to a clean whole item number
print(f"Predicted item demand for next week: {round(predicted_sales[0])} units.")
