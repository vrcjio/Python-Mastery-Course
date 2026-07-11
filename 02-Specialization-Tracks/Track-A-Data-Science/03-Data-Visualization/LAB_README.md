# 🧪 Sub-Module 03: Data Visualization Practical Lab Workbook

Welcome to your hands-on dashboard generation assignment block.

**Instructions for Students**: Open your local code workspace, create a file named `visualization_lab.py`, copy the corporate data initialization script configuration given below, and write code to fulfill the visualization objectives.

---

## 🎯 THE BUSINESS APPLICATION PROBLEM STATEMENT:
You are provided a cleaned corporate analytical dictionary tracking an retail electronics franchise's metrics containing: **Marketing Expenses, Total Sales, Store Locations, and Customer Satisfaction Scores**.

### Copy-Paste Starter Environment Code:
```python
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

print("=== Module 03: Graphical Data Journalism Lab ===")

# Cleaned data warehouse input map
franchise_metrics = {
    "Marketing_Spend_INR":,
    "Total_Sales_INR":,
    "Store_Location": ["Delhi", "Mumbai", "Delhi", "Bangalore", "Mumbai", "Bangalore", "Delhi"],
    "Satisfaction_Score": [3.8, 4.5, 4.0, 4.2, 4.8, 3.9, 4.4]
}

# Convert collection map into a DataFrame container layout
df = pd.DataFrame(franchise_metrics)
print("\n--- Input DataFrame Loaded ---")
print(df.head())

# ======================================================================
# OBJECTIVE 1: THE MARKETING EFFICIENCY SCATTER (Matplotlib figure)
# Create a scatter plot using the object-oriented fig, ax setup. 
# Plot Marketing_Spend_INR on X-axis and Total_Sales_INR on Y-axis.
# Add custom titles, grid grids, and make the points 'green' and size=80.
# ======================================================================
print("\n--- Objective 1: Building Scatter Canvas ---")

# Write your code here:



# ======================================================================
# OBJECTIVE 2: LOCATION-WISE PERFORMANCE SPLIT (Seaborn hue)
# Create a Seaborn scatter plot mapping the exact same features as Objective 1, 
# but apply the 'hue' parameter mapped onto 'Store_Location' to split 
# performance colors dynamically.
# ======================================================================
print("\n--- Objective 2: Building Seaborn Categorical Scatter ---")

# Write your code here:



# ======================================================================
# OBJECTIVE 3: THE CORRELATION GRID MAP (Heatmap)
# Calculate the correlation metrics out of the dataframe columns and 
# render a structural Seaborn Heatmap with decimals visibility enabled.
# ======================================================================
print("\n--- Objective 3: Generating Correlation Heatmap ---")

# Write your code here:


print("\n=== End of Data Visualization Lab ===")
```
