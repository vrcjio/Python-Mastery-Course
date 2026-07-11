# 📊 02: Final Specialization Blueprint Exam - Data Science & Analytics

**Duration**: 120 Minutes  
**Prerequisites**: Completion of Track A Specialization Modules (NumPy, Pandas, Visualization, SQL Pipeline).

---

## 🎯 Case Study Project: The Automated Sales Forecasting Audit

### Dataset Infrastructure Context:
You are provided two separate relational tables located inside a local database engine called `enterprise.db`:
1.  `Table: target_stores` (Columns: `Store_ID`, `Region_Zone`, `Operational_Cost`)
2.  `Table: transaction_dump` (Columns: `Tx_ID`, `Store_ID`, `Units_Sold`, `Price_Per_Unit`)

### Technical Tasks Requirements for Students:

#### Task 1: Pipeline Data Ingestion & SQL Joins (25 Marks)
Write a Python script that connects to `enterprise.db`, writes an optimized relational SQL `JOIN` statement query, and streams rows directly down into a single comprehensive Pandas DataFrame object named `raw_df`.

#### Task 2: Advanced Sieve Data Cleaning & Engineering (35 Marks)
1. Use Pandas deduplication queries to sweep out repeating transaction records.
2. Scan the columns for missing `NaN` anomalies. If `Price_Per_Unit` contains empty spaces, locate them using NumPy matrices and replace values dynamically using the column's statistical average (Mean).
3. Engineer a brand new calculated metrics field column called `Profit_Margin` utilizing vectorized math operations configuration: `Profit_Margin = (Units_Sold * Price_Per_Unit) - Operational_Cost`. (Strictly no loops allowed!).

#### Task 3: Axis Aggregations & Analytical Reductions (20 Marks)
Group your cleaned DataFrame framework by the `Region_Zone` categorical field. Compute the total aggregate sum of `Units_Sold` and global `Profit_Margin` per geographical grid. Sort the final output summary list from highest profit metrics to lowest.

#### Task 4: Graphic Insight Journalism Heatmap (20 Marks)
Instantiate an explicit object-oriented Matplotlib figure frame (`fig, ax`). Compute a correlation metrics matrix across all your numerical data fields columns, and render an interactive **Seaborn Correlation Heatmap** with annotation numbers enabled. Save the graphical canvas layout onto hard drive disk spaces as `final_insights.png`.
