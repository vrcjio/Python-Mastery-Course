# 🧪 Sub-Module 02: Interactive Signals Practical Lab Workbook

Welcome to your event-driven interactivity verification assignment block.

**Instructions for Students**: Open your local programming workspace, build a file explicitly named `signals_practice_lab.py`, copy the interactive structural shell template given below, and fill in the connectivity parameters.

---

## 🎯 OBJECTIVE 1: THE FAREWELL COUNTER CONSTRUCTOR
Design a micro incremental billing accounting simulation panel window:
1. Create a tracking text indicator (`QLabel`) showing a base numeric count value initialized flat to `0`.
2. Initialize an active operational click button (`QPushButton`) holding a stamp text named `"Increment Counter"`.

---

## 🎯 OBJECTIVE 2: BINDING SIGNALS & UI REPAIR MUTATIONS
1. Inside your window object scope class layer, create a custom python method slot named `execute_step_addition`.
2. This slot must read the present text label integer state, execute a mathematical increment markup (`+1`), and mutate the updated result back onto the visible user screen dynamically.
3. Wire your button's native `.clicked` signal conduit directly down into this method reference, avoiding any accidental execution parenthesis traps.

### Copy-Paste Starter Environment Code Template:
```python
import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QLabel, QPushButton, QVBoxLayout

class RealTimeCounterWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Telemetry Counter Engine")
        self.resize(300, 150)
        
        # Internal tracker integer state
        self.current_counter_value = 0

        # 1. Initialize your label and button widgets here:
        self.display_label = QLabel(f"Current Value: {self.current_counter_value}")
        self.add_button = QPushButton("Increment Counter")

        # 2. Arrange layout engines and mount onto center central shell:
        layout = QVBoxLayout()
        layout.addWidget(self.display_label)
        layout.addWidget(self.add_button)
        
        central_shell = QWidget()
        central_shell.setLayout(layout)
        self.setCentralWidget(central_shell)

        # 3. CONNECT your button click signal to your custom slot here:


    # 4. Define your calculation method slot here:
    def execute_step_addition(self):
        pass # Remove pass and write state increment and label mutation logic


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = RealTimeCounterWindow()
    window.show()
    sys.exit(app.exec())
```

---

## 🎯 OBJECTIVE 3: TESTING CLOUD INTEGRITY
Launch the executable application interface window. Continuous fast double-clicking across the button surface should scale the screen numeric tracker seamlessly up without freezing any main window operations.

---
