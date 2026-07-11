# 🏆 01: Mid-Term Core Python Mastery Practical Exam

**Duration**: 120 Minutes  
**Total Challenges**: 4 Production-Scale Engineering Problems  
**Instructions**: Create separate Python files for each challenge (e.g., `core_task1.py`). Write clean code following object-oriented architecture rules where required. Internet usage or copy-pasting code templates is strictly prohibited.

---

## 🚨 Challenge 1: The Automated Network Telemetry Parser
**Topics Tested**: Advanced Functions (`*args`, `**kwargs`), Loops, String Manipulations

### Problem Statement:
An automated cloud server farm sends variable telemetry strings from different node clusters. Write a unified tracking function called `parse_cluster_telemetry(*logs, **metadata)` that handles dynamic variable inputs safely:
1. The function must accept any number of raw string logs positionally (`*logs`). Each log string arrives in the strict format: `"Timestamp | Node_ID | Ping_ms"`.
2. The function must accept keyword arguments representing ecosystem metadata (`**metadata`) like `environment="Production"` or `operator="Admin"`.
3. Loop through the incoming logs stream vectorially, split the strings to extract the numeric `Ping_ms`, and compute the overall average ping latency time.
4. Print a clean, formatted report header displaying the metadata variables followed by the calculated statistics.

### Test Call Script Structure:
```python
parse_cluster_telemetry(
    "22:15:10 | NODE-A | 45",
    "22:15:15 | NODE-B | 120",
    "22:15:20 | NODE-C | 35",
    environment="Production-Cloud",
    region="Asia-South"
)
```

---

## 💾 Challenge 2: The Multi-Format Configuration Data Sync
**Topics Tested**: File Handling, CSV Operations, JSON Models, Exception Safety

### Problem Statement:
Build a standalone data utility script that parses a flat data sheet file and archives its properties permanently down into a secure JSON layout while protecting against system crash inputs:
1. The program must explicitly search your filesystem for a file named `users_dump.csv`.
2. Wrap your data streams operations inside a tight `try-except-finally` error netting block. If the CSV file does not exist, catch the `FileNotFoundError` smoothly, print an alert: `"Critical Fault: Target missing! Building clear template ledger."`, and generate a fresh empty backup file automatically.
3. If the file is active, read its rows using the default `csv` driver module, convert row data blocks into lists of nested dictionaries, and dump the state permanently into a new layout file named `users_registry.json`.
4. Utilize the **`finally`** block block to print a resource cleanup message confirming that all open file pipeline channels have closed securely.

---

## 🧱 Challenge 3: Corporate Asset Ledger System (Advanced OOPs)
**Topics Tested**: Object-Oriented Programming, Encapsulation, Inheritance, Method Overriding Polymorphism

### Problem Statement:
Design a clean corporate asset accounting backend simulation tracking software units and physical machinery. Create a multi-tier class matrix following these strict architectural guidelines:

1. **Base Class `CorporateAsset`**:
   * Constructor sets up public string `asset_name` and a strictly **Private float attribute `__base_value`**.
   * Implement a safe getter method `get_valuation()` that returns the baseline price safely.

2. **Child Class `HardwareAsset` (Inherits `CorporateAsset`)**:
   * Accepts an additional parameter `depreciation_rate` (e.g., 0.15 for 15%).
   * Uses **`super().__init__()`** to pass foundational parameters up to the parent block.
   * **Polymorphism**: Override the `get_valuation()` method block so that it computes and returns the adjusted final price after deducting the depreciation rate value from the base price.

3. **Child Class `SoftwareLicense` (Inherits `CorporateAsset`)**:
   * Accepts an additional parameter `is_expired` (Boolean).
   * **Polymorphism**: Override the `get_valuation()` method block. If `is_expired` matches True, return the asset value flat as `0.0`. If False, return the original base value.

---

## ⛔ Challenge 4: The Enterprise Matrix Guard (Custom Exceptions)
**Topics Tested**: Custom Exception Class, Explicit Runtime Validation (`raise`)

### Problem Statement:
In corporate payroll architectures, processing negative data strings or invalid wage parameters crashes database tables. Create an automated validation check script:
1. Design a custom user-defined exception class named `InvalidPayloadException` that inherits natively from the base `Exception` wrapper framework.
2. Write a verification processing function called `register_payroll_entry(employee_name, salary_amount)`.
3. If `salary_amount` is less than or equal to 0, use the **`raise`** keyword to trigger your `InvalidPayloadException` manually, passing an alert tracking string: `"Payroll Calculation Fault: Wage baseline cannot be zero or negative metrics!"`.
4. Wrap the execution testing block inside a `try-except` net. Catch your custom exception explicitly and display its error parameter message cleanly to prove the validation workflow functions perfectly.
