# 🧼 Sub-Module 02: Advanced Cleaning Mechanics, Filters & Aggregations

This documentation sheet tracks data architecture repairing pipelines, deduplications, and categorical group summary computations.

---

## 1. Handling Missing Records (`NaN` Cleaning)
Dirty corporate files have missing parameters represented inside Pandas as `NaN` (Not a Number). You can fix them using two explicit strategies:

### Strategy A: Erasing Records (Dropping)
If critical columns (like Customer Phone Numbers or Transaction IDs) are empty, drop the rows:
```python
# Drop any row that contains an empty cell in the entire dataset
clean_df = df.dropna()

# Drop rows only if the specific column 'Customer_ID' is empty
df.dropna(subset=["Customer_ID"], inplace=True)
```

### Strategy B: Dynamic Data Imputation (Filling)
If fields like 'Age' or 'Product Price' are empty, filling them with a default flag or column statistical average value preserves the data row:
```python
# Fill missing prices with a flat zero configuration
df["Price"].fillna(0, inplace=True)

# Impute missing salaries dynamically with the column average (Mean value)
average_salary = df["Salary"].mean()
df["Salary"].fillna(average_salary, inplace=True)
```

---

## 2. Deduplication & Boolean Query Filters
```python
# 1. Identify and drop exact duplicate records out of database rows instantly
df.drop_duplicates(inplace=True)

# 2. Advanced Multi-Conditional Filtering (Boolean Masking Matrix)
# Extract records where branch is West AND revenue generated is greater than 75,000
target_deals = df[(df["Branch"] == "West") & (df["Revenue"] > 75000)]
```

---

## 3. Categorical Database Splits (`groupby`)
The `.groupby()` method allows you to split the dataset table into groups based on a categorical column and compute mathematical operations on each block independently:

```python
# Group dataset by regional zone and find the exact total sum of revenue per zone
regional_revenue = df.groupby("Region")["Revenue"].sum()
print(regional_revenue)

# Find the average performance rating grouped across separate corporate designations
designation_stats = df.groupby("Designation")["Rating"].mean()
```

---
