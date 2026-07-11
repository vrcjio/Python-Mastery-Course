# 🔌 Sub-Module 01: Low-Level Connectivity & Cursor Mechanics

This guide focuses strictly on establishing standard database connections, tracking cursors, and running raw SQL statements using Python's inbuilt `sqlite3` driver.

---

## 1. Connection Framework & Cursors 🎛️
To communicate with an SQL database engine disk layout, Python requires two operational objects:
* **Connection (`conn`)**: Represents the physical wire link conduit to the target database file.
* **Cursor (`cursor`)**: Acts like an interactive pointer or blinking text terminal inside the server that executes commands and returns rows.

### Production Connection Structure:
```python
import sqlite3

# 1. Establish link to database file (Creates 'company.db' if it doesn't exist)
conn = sqlite3.connect("company.db")

# 2. Instantiate an active cursor execution agent
cursor = conn.cursor()

# 3. Always seal or close active streams when script wraps up execution
# conn.close()
```

---

## 2. Structural Schema Operations (Tables & Rows)
Open your local code editor workspace and test these fundamental structural database routines:

### A. Creating Tables and Executing Structural Schemas
```python
import sqlite3

conn = sqlite3.connect("company.db")
cursor = conn.cursor()

# Execute a raw query to create a table layout inside disk space
cursor.execute("""
CREATE TABLE IF NOT EXISTS employees (
    emp_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    salary REAL
)
""")
conn.commit() # Mandatory step to permanently save structural write modifications!
```

### B. Inserting Rows and Committing Hard Data Modifications
```python
# Inserting row tracking into the system grid database
cursor.execute("INSERT INTO employees VALUES (101, 'Rahul Verma', 45000.0)")
cursor.execute("INSERT INTO employees VALUES (102, 'Priya Sharma', 62000.0)")
conn.commit() 
```

### C. Fetching Row Data Pointers Explicitly (`fetchall`)
```python
cursor.execute("SELECT * FROM employees WHERE salary > 50000")

# Pull all matched results down into a structured python matrix list
data_rows = cursor.fetchall()
for row in data_rows:
    print(f"ID: {row[0]} | Employee Name: {row[1]} | Salary: ₹{row[2]}")
```

---

## ⚠️ Common Pitfall: The Missing Commit Lockout
When executing queries that modify structural system parameters or values (like `INSERT`, `UPDATE`, or `DELETE`), simply executing the cursor statement does not save changes to disk memory. If you forget to call `conn.commit()`, all your changes will evaporate as soon as the application terminates!

---
