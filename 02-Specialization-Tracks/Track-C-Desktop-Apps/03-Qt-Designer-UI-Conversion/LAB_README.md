# 🧪 Sub-Module 02: Qt Designer UI Compilation Lab Workbook

Welcome to your rapid UI prototyping and software compilation engineering laboratory block.

**Instructions for Students**: Launch the integrated designer framework on your workspace, build your visual components canvas according to the blueprint requirements, and compile it cleanly into python models.

---

## 🎯 OBJECTIVE 1: THE VISUAL SYSTEM TELEMETRY PROTOTYPE
Construct an internal operations panel mockup window visually using the desktop app interface:

1. Launch your layout builder tool using the system terminal call: `pyside6-designer`.
2. Open a new window canvas template choosing **"Main Window"** configuration.
3. Drag and drop these 3 core specific objects onto your canvas panel:
   * A Text Label Display (`QLabel`) -> Change its object name property metadata string to `status_header_label`.
   * A Text Line Entry Input Box (`QLineEdit`) -> Change its internal object name identifier string to `data_packet_input`.
   * An Action Trigger Button (`QPushButton`) -> Change its object name property metadata string to `transmit_telemetry_btn`.
4. Right-click on the main form layout and apply a vertical structure lock using **"Lay Out Vertically"** options. Save the blueprint file as `dashboard_view.ui`.

---

## 🎯 OBJECTIVE 2: COMPILING LAYOUT bluePRINTS INTO PYTHON SCHEMAS
Translate your structural abstract visual elements into functional executable Python script rows:

1. Open your system workspace terminal window shell right next to your saved `dashboard_view.ui` blueprint path.
2. Execute the official compilation driver command tool: **`pyside6-uic dashboard_view.ui -o ui_dashboard_view.py`**.
3. Open the newly generated `ui_dashboard_view.py` structural code asset file inside your VS Code text editor to verify that PySide6 translated your layout blocks into native Python widgets methods automatically.

---

## 🎯 OBJECTIVE 3: INTEGRATING BACKEND LOGIC SEPARATION
Connect your compiled code to your custom application logic controller system smoothly:

1. Create a fresh core file explicitly named `application_runner.py`.
2. Construct a controller sub-class class layer using multi-inheritance mapping: `class RuntimeAppController(QMainWindow, Ui_MainWindow):`.
3. Inside your constructor initialization block, trigger components mounting using **`self.setupUi(self)`**.
4. Bind the `.clicked` signal of your designer-named object button `self.transmit_telemetry_btn` directly down into a custom slot function that reads inputs from your `self.data_packet_input` line box, updating the header text instantly on execution.

---
