# 🧪 Sub-Module 03: Relational Pipeline Integration Practical Lab Workbook

Welcome to your hands-on database pipeline software automation laboratory block.

**Instructions for Students**: Open your local code workspace, create a file named `sql_pipeline_lab.py`, copy the starter data schema initialization block given down below, and write the pipeline integration code blocks to fulfill the targets.

---

## 🎯 THE BUSINESS APPLICATION PROBLEM STATEMENT:
You are provided a script template that sets up a local database file named `warehouse.db` containing transactional logistics information for a product shipping network. You need to connect Python to this server file, pull specific logs into Pandas, and export summary aggregates back into the database engine.

### Copy-Paste Starter Environment Code:
```python
import sqlite3
import pandas as pd

print("=== Module 04: Database Pipeline Engineering Lab ===")

# --- AUTOMATIC DATA ARCHITECTURE BOOTSTRAPPER ---
def bootstrap_database():
    conn = sqlite3.connect("warehouse.db")
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS shipments (
        shipment_id TEXT PRIMARY KEY,
        destination TEXT,
        weight_kg REAL,
        status TEXT
    )
    """)
    # Insert raw database telemetry records mock values
    cursor.executemany("INSERT OR REPLACE INTO shipments VALUES (?,?,?,?)", [
        ("SH101", "Delhi", 450.50, "Delivered"),
        ("SH102", "Mumbai", 1200.00, "In-Transit"),
        ("SH103", "Delhi", 850.00, "In-Transit"),
        ("SH104", "Bangalore", 340.25, "Delivered"),
        ("SH105", "Mumbai", 95.00, "Cancelled")
    ])
    conn.commit()
    conn.close()

# Run bootstrapper layout to generate warehouse.db local file structure
bootstrap_database()
print("Local Database File 'warehouse.db' Initialized with Mock Records! ⚙️")

# ======================================================================
# OBJECTIVE 1: STREAM DATA DIRECTLY INTO PANDAS
# 1. Connect Python to 'warehouse.db' using sqlite3.
# 2. Write an SQL string statement fetching columns from 'shipments'
#    where status is exactly equal to 'In-Transit'.
# 3. Use 'pd.read_sql_query' to dump rows straight into a DataFrame.
# ======================================================================
print("\n--- Objective 1: Querying In-Transit Freight Logs ---")

# Write your code here:



# ======================================================================
# OBJECTIVE 2: CALCULATE EXPORT SUMMARY
# 1. Group your queried DataFrame by 'destination' column.
# 2. Find the total sum of cargo weight ('weight_kg') for each location.
# 3. Save this computed summary framework into an object called 'summary_df'.
# ======================================================================
print("\n--- Objective 2: Computing Destination Weight Summary ---")

# Write your code here:



# ======================================================================
# OBJECTIVE 3: REVERSE PIPELINE EXPORT INGESTION
# Export your 'summary_df' data structure straight back into 'warehouse.db'
# as a permanent database table named 'transit_weight_summary'.
# Ensure old instances are replaced automatically (if_exists="replace").
# ======================================================================
print("\n--- Objective 3: Exporting Analytics Back to SQL Server ---")

# Write your code here:


print("\n=== End of Relational Pipeline Integration Lab ===")
```
