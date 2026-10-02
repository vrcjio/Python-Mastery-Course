# FastAPI Phase 3 Hands-On Industry Projects

Yeh document 2 enterprise-level projects provide karta hai jo strictly **Phase 3 (Dependency Injection, Yield Dependencies, Hierarchical Dependency Trees, Class-Based Dependencies, `pydantic-settings`, aur Router-Service-Repository Layered Architecture)** par focus karte hain.

---

# Project 1: Multi-Tier SaaS Tenant Gateway & Rate-Limiter Service

### 1. Problem Statement
Ek B2B multi-tenant SaaS platform ke liye ek API Gateway filter microservice develop karni hai. Har incoming request ko:
* Headers se Tenant ID aur API Secret verify karna hai (`extract_tenant_header` dependency).
* Tenant ke subscription tier (`Free`, `Standard`, `Enterprise`) ke basis par class-based callable rate-limiter inject karna hai.
* Ek `yield` dependency run karni hai jo request ka latency audit log record kare (request aane se lekar complete hone tak ka execution time measure karke mock telemetry pool me flush kare).

### 2. Architecture & Patterns Covered
* **Hierarchical DI Tree**: Router Dependency $\rightarrow$ Tenant Validator $\rightarrow$ Header Extractor.
* **Class-Based Callable Dependency**: `TenantRateLimiter(max_requests, window_seconds)` dynamically tier ke hisab se evaluate karega.
* **Yield Resource Dependency**: Execution telemetry timer with auto cleanup/flush.
* **Separation of Concerns**: Multi-router modular setup via `APIRouter`.

### 3. Implementation Code

```python
import time
from typing import Annotated, AsyncGenerator, Literal
from uuid import UUID, uuid4
from fastapi import APIRouter, Depends, FastAPI, Header, HTTPException, Request, status
from pydantic import BaseModel, Field

# -------------------------------------------------------------------------
# 1. Models & Schemas
# -------------------------------------------------------------------------
TenantTier = Literal["FREE", "PRO", "ENTERPRISE"]

class TenantInfo(BaseModel):
    tenant_id: str
    organization_name: str
    tier: TenantTier
    is_active: bool

class ServiceDataResponse(BaseModel):
    request_id: UUID = Field(default_factory=uuid4)
    tenant_id: str
    tier: TenantTier
    payload: str

# -------------------------------------------------------------------------
# 2. In-Memory Mock Database
# -------------------------------------------------------------------------
TENANT_REGISTRY: dict[str, TenantInfo] = {
    "org_free_101": TenantInfo(
        tenant_id="org_free_101",
        organization_name="Startup Inc",
        tier="FREE",
        is_active=True
    ),
    "org_pro_202": TenantInfo(
        tenant_id="org_pro_202",
        organization_name="Fintech Solutions",
        tier="PRO",
        is_active=True
    ),
    "org_ent_303": TenantInfo(
        tenant_id="org_ent_303",
        organization_name="Global Enterprise Corp",
        tier="ENTERPRISE",
        is_active=True
    ),
}

# In-memory sliding window request counters {tenant_id: [timestamps]}
REQUEST_HISTORY: dict[str, list[float]] = {}

# -------------------------------------------------------------------------
# 3. Layer 1: Core Dependencies (Yield & Hierarchical)
# -------------------------------------------------------------------------
async def audit_telemetry_tracker(request: Request) -> AsyncGenerator[dict, None]:
    """Yield dependency: Measures request duration and flushes metric to audit pool."""
    start_time = time.perf_counter()
    telemetry_state = {"path": request.url.path, "status": "PENDING"}
    try:
        yield telemetry_state
        telemetry_state["status"] = "SUCCESS"
    except Exception as exc:
        telemetry_state["status"] = f"FAILED: {str(exc)}"
        raise
    finally:
        duration_ms = (time.perf_counter() - start_time) * 1000
        print(f"📊 [TELEMETRY AUDIT] Path: {telemetry_state['path']} | Status: {telemetry_state['status']} | Latency: {duration_ms:.2f}ms")

def extract_api_key(x_tenant_key: Annotated[str | None, Header(description="Master Tenant Access Key")] = None) -> str:
    """Sub-dependency 1: Header extraction & format check."""
    if not x_tenant_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Mandatory header 'X-Tenant-Key' missing."
        )
    return x_tenant_key.strip()

def authenticate_tenant(
    api_key: Annotated[str, Depends(extract_api_key)]
) -> TenantInfo:
    """Sub-dependency 2: Resolves tenant credentials from store."""
    tenant = TENANT_REGISTRY.get(api_key)
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or unauthorized tenant credentials."
        )
    if not tenant.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant account is suspended."
        )
    return tenant

# -------------------------------------------------------------------------
# 4. Layer 2: Class-Based Callable Rate-Limiter Dependency
# -------------------------------------------------------------------------
class TierRateLimiter:
    """Class-based callable dependency enforcing tiered rate limits."""
    LIMIT_MAP = {
        "FREE": (3, 60),       # 3 requests per 60 seconds
        "PRO": (20, 60),      # 20 requests per 60 seconds
        "ENTERPRISE": (100, 60) # 100 requests per 60 seconds
    }

    def __call__(
        self,
        tenant: Annotated[TenantInfo, Depends(authenticate_tenant)]
    ) -> TenantInfo:
        allowed_count, window_seconds = self.LIMIT_MAP.get(tenant.tier, (3, 60))
        current_time = time.time()
        
        # Initialize or clean old timestamps
        timestamps = REQUEST_HISTORY.setdefault(tenant.tenant_id, [])
        cutoff_time = current_time - window_seconds
        REQUEST_HISTORY[tenant.tenant_id] = [t for t in timestamps if t > cutoff_time]
        
        if len(REQUEST_HISTORY[tenant.tenant_id]) >= allowed_count:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded for tier '{tenant.tier}'. Maximum {allowed_count} requests per {window_seconds}s."
            )
            
        REQUEST_HISTORY[tenant.tenant_id].append(current_time)
        return tenant

# Shared rate limiter instance
tenant_rate_gate = TierRateLimiter()

# -------------------------------------------------------------------------
# 5. Routers & Endpoints
# -------------------------------------------------------------------------
router = APIRouter(prefix="/v1/tenant-space", tags=["Tenant Secured Space"])

@router.get(
    "/data-feed",
    response_model=ServiceDataResponse,
    dependencies=[Depends(audit_telemetry_tracker)]
)
async def fetch_tenant_data_feed(
    tenant: Annotated[TenantInfo, Depends(tenant_rate_gate)]
):
    return ServiceDataResponse(
        tenant_id=tenant.tenant_id,
        tier=tenant.tier,
        payload=f"Hello {tenant.organization_name}! Secure payload delivered under {tenant.tier} tier limits."
    )

app = FastAPI(title="Multi-Tier SaaS Gateway")
app.include_router(router)
```

---

# Project 2: Decoupled E-Commerce Order & Inventory Engine (3-Tier Layered Architecture)

### 1. Problem Statement
Ek modular production-grade order processing system build karna hai jo **Strict Separation of Concerns** follow kare:
* **Routers** sirf HTTP request input/output schemas aur HTTP status codes return karenge.
* **Services** pure business domain rules handle karegi (e.g., stock sufficiency check, price calculations, item reservations).
* **Repositories** database access aur data mutations ko isolate rakhegi.
* **Settings** `pydantic-settings` ke through read honi chahiye.

### 2. Architecture & File Structure

```text
ecommerce_engine/
│
├── core/
│   ├── __init__.py
│   └── config.py               # pydantic-settings
│
├── schemas/
│   ├── __init__.py
│   └── order_schema.py         # Request / Response DTOs
│
├── repositories/
│   ├── __init__.py
│   └── inventory_repository.py # Data mutation & lookup
│
├── services/
│   ├── __init__.py
│   └── order_service.py        # Business logic & validations
│
├── routers/
│   ├── __init__.py
│   └── order_router.py         # HTTP endpoints & Depends bindings
│
└── main.py                     # App assembly
```

### 3. Implementation Code

#### 3.1 `core/config.py`
```python
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class AppConfig(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_NAME: str = "Enterprise Order Core"
    DEFAULT_TAX_RATE: float = 0.18
    MAX_ITEMS_PER_ORDER: int = 15

@lru_cache
def get_config() -> AppConfig:
    return AppConfig()
```

#### 3.2 `schemas/order_schema.py`
```python
from decimal import Decimal
from uuid import UUID, uuid4
from pydantic import BaseModel, Field

class OrderItemInput(BaseModel):
    sku: str = Field(..., min_length=3, max_length=20)
    quantity: int = Field(..., ge=1, le=50)

class CreateOrderRequest(BaseModel):
    customer_id: UUID
    items: list[OrderItemInput] = Field(..., min_length=1)

class OrderSummaryResponse(BaseModel):
    order_id: UUID
    customer_id: UUID
    subtotal: Decimal
    tax_amount: Decimal
    grand_total: Decimal
    status: str
```

#### 3.3 `repositories/inventory_repository.py`
```python
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel

class ItemRecord(BaseModel):
    sku: str
    name: str
    unit_price: Decimal
    stock: int

class InventoryRepository:
    """Simulates database transactions for inventory items."""
    def __init__(self):
        self._db: dict[str, ItemRecord] = {
            "SKU-MOCK-01": ItemRecord(sku="SKU-MOCK-01", name="Wireless Mouse", unit_price=Decimal("499.00"), stock=10),
            "SKU-MOCK-02": ItemRecord(sku="SKU-MOCK-02", name="Mechanical Keyboard", unit_price=Decimal("2499.00"), stock=5),
            "SKU-MOCK-03": ItemRecord(sku="SKU-MOCK-03", name="USB-C Hub", unit_price=Decimal("1299.00"), stock=0),
        }

    def get_by_sku(self, sku: str) -> Optional[ItemRecord]:
        return self._db.get(sku)

    def deduct_stock(self, sku: str, quantity: int) -> bool:
        item = self._db.get(sku)
        if not item or item.stock < quantity:
            return False
        item.stock -= quantity
        return True

# Repository Provider
_repo_instance = InventoryRepository()

def get_inventory_repository() -> InventoryRepository:
    return _repo_instance
```

#### 3.4 `services/order_service.py`
```python
from decimal import Decimal
from uuid import uuid4
from typing import Annotated
from fastapi import Depends, HTTPException, status

from core.config import AppConfig, get_config
from repositories.inventory_repository import InventoryRepository, get_inventory_repository
from schemas.order_schema import CreateOrderRequest, OrderSummaryResponse

class OrderService:
    def __init__(
        self,
        config: Annotated[AppConfig, Depends(get_config)],
        inventory_repo: Annotated[InventoryRepository, Depends(get_inventory_repository)]
    ):
        self.config = config
        self.repo = inventory_repo

    async def process_order(self, payload: CreateOrderRequest) -> OrderSummaryResponse:
        # Business Rule 1: Max total items check
        total_qty = sum(item.quantity for item in payload.items)
        if total_qty > self.config.MAX_ITEMS_PER_ORDER:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Order exceeds maximum items limit of {self.config.MAX_ITEMS_PER_ORDER}."
            )

        # Business Rule 2: Stock availability & price calculation
        subtotal = Decimal("0.00")
        for item in payload.items:
            record = self.repo.get_by_sku(item.sku)
            if not record:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Product with SKU '{item.sku}' not found."
                )
            if record.stock < item.quantity:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Insufficient inventory for '{record.name}'. In stock: {record.stock}"
                )
            subtotal += record.unit_price * Decimal(item.quantity)

        # Deduct stock after all validation passes
        for item in payload.items:
            self.repo.deduct_stock(item.sku, item.quantity)

        tax_rate = Decimal(str(self.config.DEFAULT_TAX_RATE))
        tax_amount = (subtotal * tax_rate).quantize(Decimal("0.01"))
        grand_total = subtotal + tax_amount

        return OrderSummaryResponse(
            order_id=uuid4(),
            customer_id=payload.customer_id,
            subtotal=subtotal,
            tax_amount=tax_amount,
            grand_total=grand_total,
            status="CONFIRMED"
        )

# Service Provider
def get_order_service(service: Annotated[OrderService, Depends()]) -> OrderService:
    return service
```

#### 3.5 `routers/order_router.py` & `main.py`
```python
# routers/order_router.py
from typing import Annotated
from fastapi import APIRouter, Depends, status
from schemas.order_schema import CreateOrderRequest, OrderSummaryResponse
from services.order_service import OrderService, get_order_service

order_router = APIRouter(prefix="/api/v1/orders", tags=["Order Fulfillment"])

@order_router.post(
    "/checkout",
    response_model=OrderSummaryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Process and Validate Customer Order"
)
async def checkout_order(
    payload: CreateOrderRequest,
    service: Annotated[OrderService, Depends(get_order_service)]
):
    return await service.process_order(payload)

# main.py
from fastapi import FastAPI

app = FastAPI(title="Decoupled E-Commerce Engine")
app.include_router(order_router)
```

---

## 4. How to Test & Verify

### Step 1: Project 1 Test (Rate-Limiter & Telemetry)
Run command:
```bash
uvicorn project1:app --reload --port 8000
```
Swagger UI khol kar `/v1/tenant-space/data-feed` execute karein with Header:
* Header `X-Tenant-Key: org_free_101` $\rightarrow$ 3 baar call karein, 4th call par `429 Too Many Requests` milega.
* Terminal me check karein: Har request ke baad `📊 [TELEMETRY AUDIT]` log print hoga with latency.

### Step 2: Project 2 Test (3-Tier Layered Architecture)
* Request body me SKU `SKU-MOCK-03` daalein (Out of stock item). Expected: `409 Conflict`.
* Quantity `20` daalein. Expected: `400 Bad Request` (Exceeds `MAX_ITEMS_PER_ORDER`).
* Valid SKU `SKU-MOCK-01` with quantity `2` order karein. Expected: `201 Created` with subtotal, calculated 18% tax, aur grand total.