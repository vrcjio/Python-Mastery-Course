# ⚙️ Capstone Web Engineering Script Blueprint

This documentation sheet holds the architectural code template blueprints and structural workspace setups required to drive your final hybrid web project assignment. 

---

## 💻 Part A: The Django REST Framework Pipeline Controller

Create a fresh file inside your Django decoupled app workspace folder named `views.py` and implement this production checkout interface tracking automated backend processing:

```python
# store/views.py - Hybrid Transaction Controller Block
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
import requests # Used to communicate with external microservices

# Dummy placeholder context models for representation purposes
# Assuming models are created as InventoryItem and CustomerTransaction

class ECommerceCheckoutViewSet(ModelViewSet):
    # Enable explicit Token-based security locks on this endpoint
    permission_classes = [IsAuthenticated]
    
    def create(self, request, *args, **kwargs):
        # 1. Capture incoming structural validation client data packet array
        client_payload = request.data
        
        # 2. Simulate standard Django ORM database save routine
        # order = CustomerTransaction.objects.create(...)
        print("[LOG]: Django ORM safely wrote transaction row data to DB disk.")
        
        # 3. FORWARD DISPATCH PIPELINE CALL TO FASTAPI ASYNC CONTEXT WORKER
        microservice_url = "http://127.0.0"
        microservice_package = {
            "transaction_id": client_payload.get("tx_id", "TX_MOCK_99"),
            "billing_amount": float(client_payload.get("amount", 0.0))
        }
        
        try:
            # Trigger network transmission payload across server terminals
            response = requests.post(microservice_url, json=microservice_package, timeout=5)
            microservice_data = response.json()
        except requests.exceptions.RequestException as e:
            microservice_data = {"status": "Microservice Pipeline Down", "error": str(e)}

        # 4. Return unified final JSON confirmation tracking status straight back to client UI
        return Response({
            "message": "Checkout state processed successfully by Django Monolith! 🎉",
            "database_status": "Committed",
            "microservice_invoice_response": microservice_data
        }, status=status.HTTP_201_CREATED)
```

---

## 💻 Part B: The FastAPI Asynchronous Invoice Microservice

Create a completely separate script workspace root directory, create a blank file named `main.py`, and implement this asynchronous type-hinted validation schema endpoint layer:

```python
# main.py - FastAPI High-Performance Async Microservices Engine
from fastapi import FastAPI, status
from pydantic import BaseModel, Field

app = FastAPI(title="Corporate Microservice Invoicing Engine")

# Define automated structural validation guidelines using Pydantic data schemas
class InvoiceDataPackage(BaseModel):
    transaction_id: str = Field(min_length=4, max_length=50)
    billing_amount: float = Field(gt=0.0, description="Amount must be a positive float sequence")

    class Config:
        json_schema_extra = {
            "example": {
                "transaction_id": "TX_9099",
                "billing_amount": 4999.50
            }
        }

# Active concurrent path route receiver endpoint handling Django server logs
@app.post("/microservice/invoice/", status_code=status.HTTP_200_OK)
async def process_async_billing_ledger(package: InvoiceDataPackage):
    # Simulate high-speed asynchronous calculations or cloud notification queues
    service_tax_markup = package.billing_amount * 0.18 # 18% Corporate Tax Calculation
    grand_total_ledger = package.billing_amount + service_tax_markup
    
    print(f"[ASYNC TELEMETRY]: Microservice looping calculations for transaction ID: {package.transaction_id}")
    
    return {
        "microservice_worker_status": "Online",
        "target_invoice_id": f"INV-{package.transaction_id}",
        "base_amount": package.billing_amount,
        "tax_calculated": round(service_tax_markup, 2),
        "final_payable_amount": round(grand_total_ledger, 2)
    }
```
