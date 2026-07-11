# 📐 Sub-Module 01: Advanced 2D Matrix Slicing & Filtering

This guide focuses strictly on structural data partitioning, dimensional inspection properties, and boolean masking techniques inside multidimensional datasets.

---

## 1. Structural Properties Inspection 🔍
Before slicing or partitioning any raw multi-dimensional matrix, you must inspect its structural boundaries using these high-utility attributes:
* **`array.ndim`**: Returns the total number of dimensions (e.g., 1D Vector = 1, 2D Matrix = 2).
* **`array.shape`**: Returns a tuple showing exact rows and columns count `(rows, columns)`.
* **`array.size`**: Returns the total number of internal elements inside the array container.
* **`array.dtype`**: Displays the exact data type allocation of the elements (e.g., `int32`, `float64`).

```python
import numpy as np

sample_matrix = np.array([[1, 2, 3], [4, 5, 6]])
print(sample_matrix.ndim)   # Output: 2
print(sample_matrix.shape)  # Output: (2, 3) -> 2 rows, 3 columns
print(sample_matrix.size)   # Output: 6 elements total
print(sample_matrix.dtype)  # Output: int64
```

---

## 2. 2D Coordinate Grid Slicing Layout
To extract specific rows, columns, or a sub-block from a 2D matrix structure, apply the following structural index accessor: `matrix[row_start:row_stop, col_start:col_stop]`.

```text
    Data Matrix Layout:
    [,  --> Row Index 0,  --> Row Index 1
      [70, 80, 90] ] --> Row Index 2

        |   |   |
      Col0 Col1 Col2
```

### Production Slicing Implementation:
```python
import numpy as np

data_matrix = np.array([,
 ,
    [70, 80, 90]
])

# 1. Slice out the entire second row (Index 1) completely
print(data_matrix[1, :])  # Output: [40 50 60]

# 2. Slice out the entire third column (Index 2) across all rows
print(data_matrix[:, 2])  # Output: [30 60 90]

# 3. Slice out a 2x2 custom sub-matrix block from top right corner
print(data_matrix[0:2, 1:3])
# Output:
# [[20 30]
#  [50 60]]
```

---

## 3. Boolean Sieve Indexing (Instant Filtering 🎯)
Never use traditional loop blocks or `if` statements to filter values out of large data matrices. Instead, apply logical expressions directly onto the indexing layer to get filtered arrays instantly.

```python
import numpy as np

raw_scores = np.array([22, 55, 88, 14, 91, 72])

# 1. Build an instant boolean condition mask
pass_mask = raw_scores > 50
print(pass_mask)  # Output: [False  True  True False  True  True]

# 2. Inject the condition mask back into the array container
filtered_output = raw_scores[pass_mask]
print(filtered_output)  # Output: [55 88 91 72]
```

---
