# 🧪 Sub-Module 02: PySide6 Multi-Threading Practical Lab Workbook

Welcome to your non-blocking system architecture and thread concurrency laboratory block.

**Instructions for Students**: Open your local programming workspace, build a script file explicitly named `async_threading_lab.py`, copy the skeleton code layout framework below, and write the multithreading logic.

---

## 🎯 OBJECTIVE 1: THE BACKEND DISPATCH THREAD ENGINE
Construct an isolated multi-threaded calculation pipeline object:
1. Define a class named `LogParsingWorker` that inherits directly from the core **`QThread`** wrapper package.
2. Setup a target percentage tracker connection using an explicit numerical data transmitter: `parsing_progress = Signal(int)`.
3. Inside your overridden `run()` method block, build a simulation counting loop from 1 to 50, emitting the active counter value step-by-step down the signal link pipeline while applying an explicit sleep check delay gap to imitate a hard file read.

---

## 🎯 OBJECTIVE 2: THE NON-BLOCKING CONTROLLER SETUP
Connect your background thread engine safely down onto your visible layout canvas structures:

1. Inside your parent window class initialization blocks, configure an interactive widget progress line (`QProgressBar`).
2. Build a local button trigger setup (`QPushButton`) that invokes a method execution block named `start_async_file_parse`.
3. Inside your trigger view slot, boot up your worker node instance using **`.start()`** mechanics, wiring the worker's native `.parsing_progress` emitter directly to your progress bar's native `.setValue` slider interface receiver block layout.

### Copy-Paste Starter Environment Code Template:
```python
import sys
import time
from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QLabel, QPushButton, QProgressBar, QVBoxLayout

# 1. Complete the background threading worker object layer here:
class LogParsingWorker(QThread):
    # Declare progress signal parameter mapping:
    pass

class NonBlockingSystemWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Relational Telemetry Pipeline Gateway")
        self.resize(400, 160)

        # UI elements initialization
        self.header = QLabel("Thread Engine Matrix: Disconnected")
        self.bar = QProgressBar()
        self.btn = QPushButton("Execute File Stream Scan")

        layout = QVBoxLayout()
        layout.addWidget(self.header)
        layout.addWidget(self.bar)
        layout.addWidget(self.btn)

        shell = QWidget()
        shell.setLayout(layout)
        self.setCentralWidget(shell)

        # Wire button click signal to your local handler slot:
        self.btn.clicked.connect(self.start_async_file_parse)

    def start_async_file_parse(self):
        self.header.setText("Thread Worker Status: Running Asynchronously... 🛰️")
        # 2. Instantiate worker, connect structural signals, and call .start() here:
        

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = NonBlockingSystemWindow()
    window.show()
    sys.exit(app.exec())
```

---

## 🎯 OBJECTIVE 3: THE LIVE WINDOW RESIZING VERIFICATION TEST
Fire up the local thread automation nodes. While the progress bar fills up steadily step-by-step via background thread worker bursts, click and drag the corners of the desktop window app to see if the interface stays completely fluid and smooth without freezing frame responses.

---
