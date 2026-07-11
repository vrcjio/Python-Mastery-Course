# 🗄️ Sub-Module 01: Data Ingestion, Inspection & Structural Selection

This guide covers the entry pipeline of loading file matrices and filtering structural columns using strict professional methods.

---

## 1. File Ingestion Engines
Pandas can pull data from multiple hard-drive sources natively. Always store the imported data inside an object named `df` (DataFrame):

```python
import pandas as pd

# Ingesting from a Comma-Separated Values file
df_csv = pd.read_csv("raw_store_data.csv")

# Ingesting from an Excel Workbook sheet explicitly
df_excel = pd.read_excel("financials.xlsx", sheet_name="Q1_Sales")
```

---

## 2. Structural Inspection Metrics 🔍
Before cleaning any data, an analyst must look at the overall dimensions and health checklist of the DataFrame using these 3 foundational tools:
* `df.head(n)`: Displays the top `n` rows of the dataset (Default is 5).
* `df.info()`: Shows the structural summary, total rows/columns count, memory usage, data types, and check for missing null parameters.
* `df.describe()`: Generates descriptive statistical metrics (Mean, Median, Standard Deviation, Max, Min) for all numerical metrics columns instantly.

---

## 3. Label Selection Selection Matrix (`.loc` vs `.iloc`)
This is the most critical checkpoint. To filter rows or columns out of a data framework, never access fields raw. Use index properties:

* **`df.loc[row_label, col_label]`**: Accesses components strictly using **text headers/labels**.
* **`df.iloc[row_position, col_position]`**: Accesses components strictly using **integer indices** (zero-indexed positions).

```python
# Assuming a DataFrame loaded with columns: 'Name', 'Age', 'Salary'

# 1. Fetch rows 0 to 4 across specific columns 'Name' and 'Salary' using label mapping
salary_sheet = df.loc[0:4, ["Name", "Salary"]]

# 2. Fetch the absolute first cell value using row 0, column 0 positionally
first_cell = df.iloc[0, 0]
```

---
