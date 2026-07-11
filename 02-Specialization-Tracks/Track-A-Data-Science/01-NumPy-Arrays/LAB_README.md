# 🧪 Sub-Module 03: NumPy Vectorization Practical Lab Workbook

Welcome to the practical lab workbook for Module 01. Below are three real-world business challenges to test your core array manipulation skills.

**Instructions for Students**: Open your local code editor, create a blank file named `my_solutions.py`, copy the starter template below, and write your code logic under the designated slots.

---

## 🎯 TASK 1: Corporate Salary Multiplier & Filter

### Problem Statement:
You are given a raw dataset containing the base salaries of 6 employees in an analytics firm. 
1. Convert the list data structure into a performance-optimized NumPy array.
2. Apply a flat **15% performance increment** across all salaries simultaneously using vectorization (Do not use loops!).
3. Use Boolean Indexing to filter out and display only those updated salaries that are strictly **greater than ₹40,000**.

### Copy-Paste Starter Code Template:
```python
import numpy as np

print("--- Task 1: Corporate Raise & Filtering Engine ---")

# Raw industrial input data list
base_salaries = [35000, 42000, 28000, 55000, 38000, 62000]

# 1. Convert to a NumPy array here:


# 2. Apply a vectorized 15% calculation markup here (Multiply by 1.15):


# 3. Create a boolean mask to filter values > 40000 here:


print("--- End of Task 1 ---")
```

---

## 🎯 TASK 2: Matrix Dimensional Broadcasting Challenge

### Problem Statement:
A retail store records base sales records for 2 different product lines across 3 distinct regions in a 2x3 grid configuration. The store manager wants to add a fixed structural zone-bonus buffer to each region. Use NumPy's automated dimensional broadcasting engine to apply the bonus across both rows simultaneously.

### Copy-Paste Starter Code Template:
```python
import numpy as np

print("--- Task 2: Matrix Dimensional Broadcasting ---")

# 2x3 Base sales data grid matrix
base_sales_matrix = np.array([,  # Product Line A
    [22000, 24000, 29000]   # Product Line B
])

# 1D Row vector containing region specific bonuses
region_bonus = np.array([1500, 2000, 2500])

# Perform vectorized matrix broadcasting addition here:
# updated_sales = ...


print("--- End of Task 2 ---")
```

---

## 🎯 TASK 3: Automated Outlier Capping Engine (`np.where`)

### Problem Statement:
You are monitoring an automated web application data stream tracking continuous network telemetry latency records. 
1. Generate a continuous array sequence from 10 to 100 with a step jump of 10 (`10, 20, 30... 100`).
2. Use the high-speed conditional structural function `np.where()` to create a clean tracking data line where any latency calculation **greater than 60** is capped flat to `60`, while everything else stays unchanged. (Do not use slow python loops or if-else statements).

### Copy-Paste Starter Code Template:
```python
import numpy as np

print("--- Task 3: Vectorized Outlier Capper ---")

# 1. Generate array sequence layout from 10 to 100 using np.arange():
# data_stream = ...

# 2. Apply np.where() logic here to cap numbers at 60:
# clean_stream = ...


print("--- End of Task 3 ---")
```
