# 🧪 Sub-Module 02: Django REST Framework API Engineering Lab Workbook

Welcome to your production API engineering architecture laboratory block.

**Instructions for Students**: Open your local workspace instance, import the standard DRF components engine inside your application layout layers, and configure endpoints according to the parameters.

---

## 🎯 OBJECTIVE 1: LOGISTICS TRACKING SERIALIZATION INTERFACE
Configure a dedicated REST endpoint layer over the `OrderRegistry` model mapping we built inside Module 02:

1. Create a specialized script workspace file explicitly named `store/serializers.py`.
2. Construct a `ModelSerializer` sub-class named `OrderRegistrySerializer` tracking specifically these fields: `id`, `order_date`, and `invoice_amount`. Ensure internal customer IDs are excluded from surface network packets.
3. Configure a views controller class engine named `OrderRegistryViewSet` driving operations on top of your model query layers.

---

## 🎯 OBJECTIVE 2: THE REST TERMINAL ROUTING INTEGRATION
Inject automated URL maps using the integrated `DefaultRouter` abstraction layouts:

1. Register your `OrderRegistryViewSet` routing controller map under a text query pattern string named `'orders'`.
2. Run your local server container and fire up the native REST dashboard panels.
3. Use integrated API interface tools (or local shell curl configurations) to execute a safe mock **`POST` HTTP request** containing a JSON data package array to insert a new order record dynamically inside memory:
   ```json
   {
       "invoice_amount": "7450.00"
   }
   ```

---

## 🎯 OBJECTIVE 3: THE IMMUTABLE DATA CHECKPOINT
Modify your serializer fields configuration to declare `order_date` as a strictly **`read_only=True`** parameter block layout, ensuring no external client API call can hijack or alter invoice date metrics manually inside production pipelines.

---
