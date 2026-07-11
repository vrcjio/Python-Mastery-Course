# ⚙️ Capstone Desktop Systems Engineering Script Blueprint

This documentation sheet holds the high-density architectural code template blueprint and structural thread communications required to drive your final cross-platform native software project assignment.

---

## 💻 The Production-Grade Cross-Thread App Architecture

Create a fresh file inside your local application directory project folder named `billing_system_app.py`, copy this template inside it, and implement your target backend math logic inside the designated slots placeholder hooks:

```python
import sys
import time
# Importing strict PySide6 cross-platform systems engineering components
from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QLabel, QLineEdit, QPushButton, QProgressBar, QVBoxLayout, QHBoxLayout

# ======================================================================
# ⚙️ PART A: THE BACKGROUND COMPACT ACCOUNTING ENGINE (THREAD ISOLATION)
# Objective: Offload loop operations from the UI screen space into a QThread.
# ======================================================================
class BusinessAuditWorker(QThread):
    # Setup thread-safe data transmitter channels explicitly using Core Signals
    step_signal = Signal(int)
    log_signal = Signal(str)

    def __init__(self, raw_amount, items_count):
        super().__init__()
        self.raw_amount = raw_amount
        self.items_count = items_count

    def run(self):
        """Core corporate inventory calculations and math logging loop."""
        self.log_signal.emit("Initializing Inventory Calculation Pipeline...")
        time.sleep(0.5)

        # Vector step countdown simulation simulation loop
        for progress_index in range(1, 101):
            time.sleep(0.03) # Simulating heavy disk data write matrices calculations
            self.step_signal.emit(progress_index) # Broadcast completion bar data live

        # Compute final invoice math metrics out of inputs parameters safely
        base_payable = self.raw_amount * self.items_count
        tax_applied = base_payable * 0.18 # 18% Corporate GST standard markup calculation
        net_payable_amount = base_payable + tax_applied

        success_log_string = f"Invoice Compiled Successfully! Total Payable (Incl. 18% Tax): INR {net_payable_amount:.2f}"
        self.log_signal.emit(success_log_string)

# ======================================================================
# 🏁 PART B: THE DUAL-STACK RESPONSIVE USER INTERFACE (MAIN WINDOW FRAME)
# Objective: Handle layout scaling, signals mappings, and thread link loops.
# ======================================================================
class StandaloneBillingWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Industrial POS Terminal Core v2.4")
        self.resize(500, 240)

        # 1. Instantiate structural inputs lines and labels widgets
        self.status_header = QLabel("Terminal Status: Ready for Entry Session")
        self.status_header.setStyleSheet("font-weight: bold; color: #2c3e50;")
        
        self.amount_lbl = QLabel("Item Unit Price:")
        self.amount_input = QLineEdit("500.00") # Preset dummy numeric placeholder text
        
        self.quantity_lbl = QLabel("Total Items Count:")
        self.quantity_input = QLineEdit("5")     # Preset dummy numeric placeholder text
        
        self.progress_bar = QProgressBar()
        self.checkout_trigger_btn = QPushButton("Finalize Secure Corporate Audit")

        # 2. Build fluid layout matrix blocks
        input_row_box = QHBoxLayout()
        input_row_box.addWidget(self.amount_lbl)
        input_row_box.addWidget(self.amount_input)
        input_row_box.addWidget(self.quantity_lbl)
        input_row_box.addWidget(self.quantity_input)

        master_vertical_stack = QVBoxLayout()
        master_vertical_stack.addWidget(self.status_header)
        master_vertical_stack.addLayout(input_row_box) # Nesting horizontal line inside vertical panel
        master_vertical_stack.addWidget(self.progress_bar)
        master_vertical_stack.addWidget(self.checkout_trigger_btn)

        # Bind structural view model canvas onto a blank Central widget shell
        central_shell_widget = QWidget()
        central_shell_widget.setLayout(master_vertical_stack)
        self.setCentralWidget(central_shell_widget)

        # 3. INTERACTIVITY WIRE: Connect click signal avoiding brackets call traps
        self.checkout_trigger_btn.clicked.connect(self.start_billing_thread_pipeline)

    def start_billing_thread_pipeline(self):
        """Extracts values, safely handles interface locks, and boots thread paths."""
        try:
            # Parse text fields values securely using explicit numeric conversions casting
            input_price = float(self.amount_input.text().strip())
            input_count = int(self.quantity_input.text().strip())
        except ValueError:
            self.status_header.setText("Terminal Exception ⚠️: Invalid numeric value entries formatting!")
            return

        # Disable button view elements to eliminate parallel tracking cross-trigger hazards
        self.checkout_trigger_btn.setEnabled(False)
        self.progress_bar.setValue(0)

        # 4. INSTANTIATE AND RUN THE DECOUPLED PIPELINE WORKER NODE
        self.thread_worker = BusinessAuditWorker(input_price, input_count)

        # Connect background worker signals directly down onto main thread UI elements modifiers slots
        self.thread_worker.step_signal.connect(self.progress_bar.setValue)
        self.thread_worker.log_signal.connect(self.status_header.setText)
        
        # Attach cleanup callback slot to reset user control loops safely upon task wrap-up
        self.thread_worker.finished.connect(lambda: self.checkout_trigger_btn.setEnabled(True))

        # Launch the independent background runtime execution channel loop context
        self.thread_worker.start()

if __name__ == "__main__":
    # Boot operating system interactions conduit loop
    app = QApplication(sys.argv)
    window = StandaloneBillingWindow()
    window.show()
    sys.exit(app.exec())
```
