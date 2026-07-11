# 💻 04: Final Specialization Blueprint Exam - Desktop Application Engineering

**Duration**: 120 Minutes  
**Prerequisites**: Completion of Track C Specialization Modules (PySide6 Layouts, Signals, Designer, QThread).

---

## 🎯 Case Study Project: Standalone Industrial Telemetry POS Terminal Dashboard

### Technical Tasks Requirements for Students:

#### Task 1: Responsive Layout Core Mesh Canvas (25 Marks)
Using strict **PySide6 standard import layouts** natively inside an object-oriented subclass window class, initialize an active dashboard dashboard framework window inheriting from `QMainWindow`:
1. Create user view elements tracking widgets: A text indicator header (`QLabel`), a numerical entry line box (`QLineEdit`), a progress layout view slider (`QProgressBar`), and an execution button (`QPushButton`).
2. Arrange elements dynamically without hard-coding absolute pixel coordinates: Stack inputs horizontally side-by-side using `QHBoxLayout`, and anchor them over a global layout engine vertical stack (`QVBoxLayout`) to ensure responsive scaling window resizing.

#### Task 2: Interactivity Handlers & Signals Wire Map (25 Marks)
Connect your action button's native `.clicked` event signal directly down onto a custom logic handler view method slot inside your window object scope. Ensure you pass the function reference safely without immediate evaluation parenthesis traps `()`. The slot must dynamically extract text properties out of inputs box containers using parsing hooks (`.text().strip()`).

#### Task 3: Non-Blocking Background Concurrency Thread (QThread) (35 Marks)
1. Isolate processing layers cleanly by constructing an independent multi-threading worker object subclass inheriting from **`QThread`**.
2. Offload a heavy 50-step loop execution matrix task parameter inside the worker's `.run()` environment block loop method.
3. Instantiate a custom tracker signal `progress_emitter = Signal(int)` inside the thread scope class layout. Use `.emit()` to broadcast percentage data line bursts back to the main thread smoothly.

#### Task 4: Thread-Safe UI Mutation Connections (15 Marks)
Connect your background thread worker signals directly onto the main view canvas progress bar setValue slider modifier slot. Launch your processing worker node using **`.start()`** mechanics. Manually drag window corners with cursor frames while loop processes execute to prove that your application frame remains 100% fluid, responsive, and free from operating system freeze hang alerts!
