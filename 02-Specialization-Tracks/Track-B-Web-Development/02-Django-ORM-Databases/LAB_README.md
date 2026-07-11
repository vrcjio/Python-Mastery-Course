# 🧪 Sub-Module 02: Django ORM & Database Schema Lab Workbook

Welcome to your relational database mapping and optimization laboratory block. 

**Instructions for Students**: Open your local Django environment project, navigate to your app workspace layer, and configure your system database schemas according to the target parameters.

---

## 🎯 OBJECTIVE 1: THE E-COMMERCE CART SCHEMA SYSTEM
Design a multi-tier database model configuration representing an internal user warehouse tracking module inside `models.py`:

1. Create a class model named `CustomerProfile` with fields: `full_name` (Text up to 150 characters) and `email_id` (Explicitly configured as a unique string identifier).
2. Create a class model named `OrderRegistry` with fields:
   * `customer` -> Setup a `ForeignKey` link pointing to `CustomerProfile`. If a customer profile gets wiped out, block its deletion parameter (`on_delete=models.PROTECT`).
   * `order_date` -> Auto-populate the date value dynamically on entry creation (`auto_now_add=True`).
   * `invoice_amount` -> Set up an optimized Decimal data layout supporting maximum 12 digits and 2 decimal points precision.

---

## 🎯 OBJECTIVE 2: BLUEPRINT RUNTIME COMPILATION
Execute the proper environment pipeline sequence to hard write these schemas onto your SQL storage database:
1. Run terminal commands to cross-check structural syntax checks and build intermediate python script migration logs.
2. Apply the compiled migration files straight down onto your active SQLite or PostgreSQL engines.
3. Open the Django admin control system dashboard pane or access `python manage.py shell` to manually insert 2 customers and 3 matching order rows safely.

---

## 🎯 OBJECTIVE 3: THE OPTIMIZED FILTER ASSIGNMENT
Inside a clean view function layer or shell playground, write a vectorized Python QuerySet operation that extracts and logs every order row where the `invoice_amount` is **greater than ₹5,000**, utilizing **`select_related()`** to completely eliminate any potential N+1 relational memory leak loops.

---
