# 📊 Sub-Module 01: Low-Level Architecture & Fundamental Plots

This guide focuses strictly on the layout anatomy of a figure canvas and plotting foundational structural charts using Matplotlib.

---

## 1. Anatomy of a Plot (The Object-Oriented Framework) 📐
Never use the raw `plt.plot()` configuration for large data projects. Always instantiate a concrete Figure (`fig`) container and an Axis (`ax`) tracking coordinate framework explicitly using `plt.subplots()`:

* **Figure (`fig`)**: The main outer blank cardboard sheet frame window that contains your charts.
* **Axes (`ax`)**: The actual specific internal mathematical coordinate block layout inside the cardboard where data points are drawn.

```python
import matplotlib.pyplot as plt

# Create a clean canvas structure window containing 1 row and 1 column
fig, ax = plt.subplots(figsize=(8, 4)) # Width=8 inches, Height=4 inches

# All drawing commands happen directly on the 'ax' object
ax.set_title("Corporate Revenue Curve")
ax.set_xlabel("Timeline Months")
ax.set_ylabel("Revenue in USD")

plt.show() # Renders canvas frame to screen
```

---

## 2. Fundamental Chart Configurations
Open your local code editor workspace and test these foundational vector plotting mechanics:

### A. Line Plots (Tracking Trends Over Time)
```python
months = ["Jan", "Feb", "Mar", "Apr"]
sales = [12000, 15000, 14000, 19000]

fig, ax = plt.subplots()
ax.plot(months, sales, color="blue", marker="o", linestyle="--", linewidth=2)
ax.grid(True, linestyle=":", alpha=0.6) # Add structural mesh background
```

### B. Bar Charts (Comparing Discrete Categories)
```python
products = ["Laptops", "Mice", "Keyboards"]
units_sold = [450, 1200, 850]

fig, ax = plt.subplots()
ax.bar(products, units_sold, color=["indigo", "orange", "teal"])
```

### C. Scatter Plots (Inspecting Relationships Between Variables)
```python
advertising_budget = [1000, 2000, 3000, 4000]
store_footfall = [150, 280, 390, 510]

fig, ax = plt.subplots()
ax.scatter(advertising_budget, store_footfall, color="crimson", s=100) # s=Size of dots
```

---

## ⚠️ Common Pitfall: The Overlapping Legends Clutter
When plotting multiple lines or bars on the same layout canvas, adding an automated legend statement without explicit placement markers can clip your charts. Always direct placement explicitly using the `loc` string parameters:
```python
#   THE PLACEMENT REPAIR WAY:
ax.legend(["Branch A", "Branch B"], loc="upper right", bbox_to_anchor=(1, 1))
```

---
