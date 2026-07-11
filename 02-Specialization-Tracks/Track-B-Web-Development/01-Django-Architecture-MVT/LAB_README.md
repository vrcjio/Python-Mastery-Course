# 🧪 Sub-Module 02: Django Architecture Practical Lab Workbook

Welcome to your hands-on Django layout verification assignment. 

**Instructions for Students**: Open your system environment shell workspace, initialize a fresh web architecture using the guidelines below, and verify the deployment output endpoints.

---

## 🎯 OBJECTIVE 1: MODULAR PROJECT INITIALIZATION
1. Create a local environment workspace directory structure.
2. Initialize a Django configuration module named `campus_portal`.
3. Create an internal component sub-app named `academics`.
4. Register the `academics` configuration properly inside your system settings grid.

---

## 🎯 OBJECTIVE 2: ISOLATED APP ROUTING PIPELINE
Instead of adding your path rules inside the main project script layout, decouple them by setting up an independent local url infrastructure:

1. Create a fresh file explicitly named `academics/urls.py`.
2. Inside `academics/views.py`, write a function configuration named `course_index_view` that returns a plain HTTP payload layout string: `"Welcome to Academics Course Matrix Directory Database! 📚"`.
3. Map this view to the local empty endpoint index routing rule `path('', course_index_view)`.
4. Link this local routing tree into the parent tracking index `campus_portal/urls.py` file under a base URL string named `'portal/'`.

### Expected Validation Verification Checkpoint:
When you run `python manage.py runserver`, hitting `http://127.0.0` should return a 404 system error safely (because root is empty), but surfing straight to **`http://127.0.0portal/`** should return your message string seamlessly!

---

## 🎯 OBJECTIVE 3: THE REVERSE TESTING BLOCK
Write an alternative template file path route rule named `portal/status/` that returns a clean dashboard server execution confirmation text message alongside the current live timeline string.

---
