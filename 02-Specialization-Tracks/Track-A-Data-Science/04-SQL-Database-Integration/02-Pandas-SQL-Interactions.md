# 🐼 Sub-Module 02: High-Level Pandas Interactivity & Data Exporting

This documentation sheet tracks advanced analytical loading operations and automated DataFrame storage writing pipelines using Pandas.

---

## 1. Automated Query Ingestion (`pd.read_sql_query`)
Writing loops around `cursor.fetchall()` is slow and messy. Pandas provides a high-speed unified driver function that passes an SQL query string to the backend, pulls the database metrics rows, and automatically converts them into a labeled DataFrame with correct column headers in one single line:

```python
import sqlite3
import pandas as pd

conn = sqlite3.connect("company.db")

# Define target query string syntax
sql_query = "SELECT name, salary FROM employees WHERE salary >= 50000"

# Pull data straight into a structured data frame container
df = pd.read_sql_query(sql_query, conn)
print(df.head()) # Instantly mapped with headers!
conn.close()
```

---

## 2. Reverse Data Pipeline Engineering (`df.to_sql`) 📥
When you finish clean manipulations or compute data science predictions, you can dump the entire updated DataFrame table straight back into the database as a permanent table:

```python
# Assuming 'clean_df' is a modified DataFrame you want to store in database files

# Dump data framework as a fresh structural table named 'processed_sales'
clean_df.to_sql("processed_sales", conn, if_exists="replace", index=False)

# Parameters Explained:
# if_exists="replace" -> Drops old table layout if it matches name and writes a fresh one.
# if_exists="append"  -> Inserts rows at the bottom without altering original setups.
# index=False         -> Drops default Pandas row numbers from being stored as a column.
```

---
