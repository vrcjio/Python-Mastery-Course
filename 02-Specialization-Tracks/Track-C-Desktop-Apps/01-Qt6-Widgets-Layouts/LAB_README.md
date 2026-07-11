# 🧪 Sub-Module 02: PySide6 Layouts Practical Lab Workbook

Welcome to your hands-on desktop systems engineering laboratory assignment block. 

**Instructions for Students**: Open your local code workspace directory layer, create a fresh file explicitly named `desktop_layout_lab.py`, copy the starter template below, and write code to fulfill the objectives.

---

## 🎯 OBJECTIVE 1: THE ENTERPRISE PROFILE INTERFACE
Design a multi-layer responsive input panel structure inside a custom `QMainWindow` object sub-class:

1. Create a text field label widget (`QLabel`) showing your institute's name parameter.
2. Initialize two discrete inline user text inputs fields utilizing the **`QLineEdit`** core widget to collect username profiles.
3. Configure a confirmation execution button (`QPushButton`) holding a text stamp named `"Authenticate Session"`.

---

## 🎯 OBJECTIVE 2: THE DUAL-STACK MIXED LAYOUT CONFIGURATION
Arrange the custom widgets systematically without hard-coding pixel locations layout bounds:

1. Instantiate a horizontal layout manager (`QHBoxLayout`) and place your two text input field line boxes inside it side-by-side.
2. Instantiate a master vertical layout engine (`QVBoxLayout`).
3. Add your main text heading label at the absolute top, nest your nested horizontal layout box directly inside it underneath, and mount the authentication button at the bottom slot.
4. Bind this vertical structural pipeline onto a custom blank widget wrapper shell, and route it to the center using `.setCentralWidget()`.

### Copy-Paste Starter Environment Code Template:
```python
import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton

class UserAuthenticationWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Secure Gateway Portal")
        self.resize(450, 200)

        # 1. Initialize your core widgets here (QLabel, QLineEdit, QPushButton):


        # 2. Setup your layout engines (QVBoxLayout, QHBoxLayout):


        # 3. Nest layouts and bind onto central widget shell here:


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = UserAuthenticationWindow()
    window.show()
    sys.exit(app.exec())
```

---

## 🎯 OBJECTIVE 3: RENDER ANALYSIS RUNTIME
Launch the local desktop execution engine. Resize the boundaries manually using your cursor to cross-examine if the text fields expand and scale their layouts responsively across the canvas grid.

---
