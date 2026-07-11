# 🌐 03: Final Specialization Blueprint Exam - Full-Stack Web Development

**Duration**: 120 Minutes  
**Prerequisites**: Completion of Track B Specialization Modules (Django MVT, ORM, REST Framework, FastAPI).

---

## 🎯 Case Study Project: Decoupled Multi-Tenant Corporate Inventory Gateway

### Technical Tasks Requirements for Students:

#### Task 1: Relational Schema Mapping Architecture (30 Marks)
Inside a fresh Django application workspace layer, build two linked relational models inside `models.py`:
1.  `Class SupplierProfile`: Fields include `company_name` (Text) and a unique tracking string field `registry_code`.
2.  `Class StockComponent`: Fields include `item_name`, `sku_string` (unique text configuration), and `current_units`. Build a Foreign Key relationship connecting it back to `SupplierProfile`. If a supplier profile is deleted, explicitly prevent the deletion parameter (`on_delete=models.PROTECT`).

#### Task 2: DRF ModelViewSet Endpoint Routing (25 Marks)
1. Construct an explicit `ModelSerializer` container block in `serializers.py` mapping structural stock attributes into direct JSON text arrays. Avoid using unmapped open variables (`__all__`).
2. Expose this endpoint logic using a standard `ModelViewSet` register pattern driven inside a router architecture accessible under path patterns string `api/warehouse/`.

#### Task 3: Token Authorization Route Security Guard (20 Marks)
Lock down your newly exposed api path routing lines completely. Implement Django's integrated token verification handlers (`TokenAuthentication`). Ensure any global untracked request call hitting the warehouse route receives a strict `403 Forbidden` status payload unless they submit a valid authorization header value token.

#### Task 4: Asynchronous Dispatch Notification Hook (FastAPI) (25 Marks)
1. Inside an independent microservices module path directory, initialize an active asynchronous **FastAPI service container application** script (`main.py`).
2. Establish an asynchronous receiver routing view endpoint rule: `@app.post("/async/alert/")`.
3. Use Pydantic input models structures to receive a validation payload from Django containing the updated inventory item parameters. Re-route the task loop concurrently to simulate an external cloud notifications server, and check validation diagnostics natively using the interactive Swagger UI panel endpoint block.
