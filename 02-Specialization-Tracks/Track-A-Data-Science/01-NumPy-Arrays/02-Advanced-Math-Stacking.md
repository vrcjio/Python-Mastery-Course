# 🥞 Sub-Module 02: Structural Math, Broadcasting & Stacking Pipelines

This section covers production mathematical aggregations, vector stitching pipelines, and dimensional scale expansion layout operations.

---

## 1. Axis-Wise Structural Reductions (`axis=0` vs `axis=1`)
When running mathematical aggregates (like `.sum()`, `.mean()`) on multi-dimensional matrices, you must explicitly pass the direction parameter:
* **`axis=0`**: Computes calculations **Vertically down columns**.
* **`axis=1`**: Computes calculations **Horizontally across rows**.

```python
import numpy as np

matrix_data = np.array([,
    [30, 40]
])

print(np.sum(matrix_data, axis=0)) # Column totals down vertical -> Output: [40 60]
print(np.sum(matrix_data, axis=1)) # Row totals across horizontal -> Output: [30 70]
```

---

## 2. The Multi-Dimensional Broadcasting Rule 📡
When adding or multiplying arrays of completely mismatched dimensions, NumPy stretches the smaller array automatically across rows or columns to execute vector arithmetic without creating heavy duplicate copies in the memory cache.

```python
import numpy as np

base_grid = np.array([,
    [30, 40]
])
row_adder = np.array([1, 2])

# row_adder (1D array) automatically broadcasts across both rows of the 2D grid matrix
print(base_grid + row_adder)
# Output:
# [[11 22]
#  [31 42]]
```

---

## 3. Multi-Dimensional Array Initializers (Data Generation ⚙️)
In real software development, we often need placeholder metrics templates or dummy vector spacing elements built dynamically inside RAM memory:
* `np.zeros((rows, cols))`: Returns an array grid packed with floating zeros `0.0`.
* `np.ones((rows, cols))`: Returns an array grid packed with floating ones `1.0`.
* `np.linspace(start, stop, num)`: Generates `num` numbers evenly spaced out across a specific continuous range line. (Crucial for statistical coordinate curves).

```python
import numpy as np

# Generate 5 numbers evenly spaced between 0 and 10
grid_line = np.linspace(0, 10, 5)
print(grid_line) # Output: [ 0.   2.5  5.   7.5 10. ]
```

---

## 4. De-duplication & Mapping Engines (`np.unique` & `np.where`)
* **`np.unique(arr)`**: Instantly filters out duplicate items across any single or multidimensional data layer and returns a clean, sorted unique sequence list.
* **`np.where(condition, value_if_true, value_if_false)`**: Acts as a high-speed vectorized conditional replacer. No loops needed.

```python
import numpy as np

metrics = np.array([15, 75, 20, 90])

# Conditional capping: If element value > 50, map to 50, else leave untouched
clean_metrics = np.where(metrics > 50, 50, metrics)
print(clean_metrics) # Output: [15 50 20 50]
```

---

## 5. Structural Data Merging & Concatenation (`vstack` & `hstack`)
Stitch completely independent data source pipelines together using structural physical bonding operations:
* **`np.vstack()`**: Vertical Stacking (stacks rows underneath each other).
* **`np.hstack()`**: Horizontal Stacking (attaches columns side-by-side).

```python
import numpy as np

line_a = np.array([1, 2, 3])
line_b = np.array([4, 5, 6])

print(np.vstack((line_a, line_b))) 
# Output: 
# [[1 2 3]
#  [4 5 6]]
```
