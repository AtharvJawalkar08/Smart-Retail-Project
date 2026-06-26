install.packages("blob", repos = "https://r-project.org")

# ==========================================
# STEP 1: LOAD DATABASE TOOLS
# ==========================================
# R has standard built-in packages to talk to databases.
# 'RSQLite' lets R read our '.db' file directly.
library(RSQLite)

# ==========================================
# STEP 2: CONNECT TO THE SQL DATABASE
# ==========================================
# We tell R to wake up the SQLite driver and open our file.
db_driver <- dbDriver("SQLite")
connection <- dbConnect(db_driver, dbname = "retail_store.db")

# ==========================================
# STEP 3: EXTRACT TOTAL DAILY SALES WITH SQL
# ==========================================
# We write a standard SQL query string. 
# This adds up ('SUM') all products sold grouped by each unique calendar day.
query <- "
  SELECT sale_date, SUM(quantity_sold) as total_sales 
  FROM sales_transactions 
  GROUP BY sale_date 
  ORDER BY sale_date;
"

# Send the query into the database file and fetch the clean results table.
sales_history <- dbGetQuery(connection, query)

# Clean up: Close the database connection safely.
dbDisconnect(connection)

# ==========================================
# STEP 4: PRINT THE DATA IN THE TERMINAL
# ==========================================
# Let's print out what R found so we can see it with our eyes.
print("--- Historical Data Retrived from SQL ---")
print(sales_history)

# ==========================================
# STEP 5: VISUALISE THE DEMAND SPIKE
# ==========================================
# R has an excellent built-in charting system.
# 'plot' creates a line graph ('type = o' means lines with dots).
# 'main' sets the chart title, 'xlab' is the bottom label, 'ylab' is the side label.
plot(
  x = 1:nrow(sales_history), 
  y = sales_history$total_sales, 
  type = "o", 
  col = "blue",
  main = "Daily Store Demand Trends",
  xlab = "Timeline (Days)",
  ylab = "Total Units Sold"
)
