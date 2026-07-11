# 🔥 Sub-Module 02: High-Level Statistical Inferences & Density Maps

This documentation sheet tracks advanced analytical graphs, distribution spreads, and multi-variable structural map plotting using Seaborn.

---

## 1. Categorical Breakdown Engineering (`hue` Tracking)
Seaborn allows you to pass a Pandas DataFrame straight to the layout engine and automatically split data variables visually based on a third categorical category string using the **`hue`** mapping parameter:

```python
import seaborn as sns
import matplotlib.pyplot as plt

# Sample DataFrame setup containing 3 features
# df loaded with columns: 'Experience', 'Salary', 'Gender'

# Scatter plot tracking Salary vs Experience, segmented automatically by Gender colors
sns.scatterplot(data=df, x="Experience", y="Salary", hue="Gender", palette="Set1")
plt.show()
```

---

## 2. Data Distribution & Anomaly Mapping (Box Plots) 📦
When analyzing datasets, identifying data distribution shapes and data outliers is mandatory.
* **Box Plot (Whisker Plot)**: Visually displays the Median, Quartiles, and isolates extreme values (Outliers) as discrete external dots instantly.

```python
# Create a statistical box plot checking 'Salary' spreads grouped across separate 'Departments'
sns.boxplot(data=df, x="Department", y="Salary", palette="pastel")
```

---

## 3. The Industrial Matrix Insight: Correlation Heatmaps 🔥
Before training any Machine Learning prediction algorithms, data engineers inspect correlations to check how numerical columns relate to each other.
* If correlation is close to `1.0`: The columns have a perfect positive relationship.
* If correlation is close to `0.0`: No relationship exists.

```python
# 1. Compute numerical calculation matrix matrix out of raw DataFrame
correlation_matrix = df.corr(numeric_only=True)

# 2. Draw an automated visual heatmap grid
sns.heatmap(correlation_matrix, annot=True, cmap="coolwarm", fmt=".2f", linewidths=0.5)
# annot=True inserts exact decimal values inside each block box grid
```

---
