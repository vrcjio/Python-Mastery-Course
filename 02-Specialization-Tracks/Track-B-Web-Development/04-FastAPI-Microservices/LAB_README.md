# 🧪 Sub-Module 02: Asynchronous Microservice Engineering Lab Workbook

Welcome to your production FastAPI microservice application engineering laboratory block.

**Instructions for Students**: Create an independent workspace directory, set up your async server instances using the guidelines below, and utilize the interactive Swagger UI interface to test input data models execution rules.

---

## 🎯 OBJECTIVE 1: CLOUD APPLICATION CONFIGURATION INFRASTRUCTURE
Design a secure, optimized data pipeline endpoint configuration representing an cloud metric tracking system:

1. Create a script file explicitly named `main.py`.
2. Instantiate a core `FastAPI()` application engine layer configuration.
3. Construct a Pydantic operational validation class schema named `TelemetryPackage` verifying these explicit properties:
   * `device_id` -> A strict string identifier that must contain at least 4 characters (`min_length=4`).
   * `core_temperature` -> A mandatory floating-point numerical parameter block.
   * `is_active` -> An explicit boolean data flag default value configuration (`default=True`).

---

## 🎯 OBJECTIVE 2: THE CONCURRENT API PATH ROUTE
Build an active asynchronous execution routing view endpoint handling incoming client server requests:

1. Write an asynchronous controller framework block named `capture_telemetry_stream` mapped onto the path route string pattern: `@app.post("/telemetry/log/")`.
2. Ensure the method catches the validated `TelemetryPackage` inputs safely inside runtime memory.
3. Return an automated secure response packet matching this format block structure:
   ```json
   {
       "device_captured": "DEV-4001",
       "status_logged": "Success",
       "safety_margin": 12.50
   }
   ```

---

## 🎯 OBJECTIVE 3: INTERACTIVE SWAGGER INTERFACE TEST RUN
1. Launch your microservice server nodes inside your environment terminal utilizing the `uvicorn` engine.
2. Surfing straight to **`http://127.0.0`**, trigger the local interactive pane tool, and write a mock validation test case body.
3. Intentionally execute a faulty request payload passing an integer structure inside the string array properties to verify that FastAPI's core engine throws a robust, secure **`422 Unprocessable Entity`** error validation schema log packet automatically.

---
