# FastAPI Phase 3 Developer Handbook: Dependency Injection & Modular Architecture

Yeh handbook FastAPI ke sabse powerful core feature—**Dependency Injection (DI)**—aur enterprise-level **Layered Architecture (Separation of Concerns)** ka production reference guide hai.

---

## 1. Dependency Injection (DI) Fundamentals

FastAPI ka DI system reusable logic, authentication checks, database sessions, aur external service clients ko endpoints me inject karne ka primary mechanism hai. Yeh **Inversion of Control (IoC)** principle follow karta hai.

### 1.1 `Depends()` Syntax & Execution Flow

```python
from typing import Annotated
from fastapi import FastAPI, Depends

app = FastAPI()

# 1. Common Query Parameter Dependency
def common_pagination_params(
    page: int = 1,
    limit: int = 20
) -> dict[str, int]:
    clamped_limit = min(limit, 100)
    offset = (page - 1) * clamped_limit
    return {"page": page, "limit": clamped_limit, "offset": offset}

# Type alias with Annotated
PaginationDep = Annotated[dict[str, int], Depends(common_pagination_params)]

@app.get("/items")
async def list_items(pagination: PaginationDep):
    return {
        "page": pagination["page"],
        "limit": pagination["limit"],
        "offset": pagination["offset"]
    }
```

---

## 2. Advanced Dependency Patterns

### 2.1 Yield Dependencies (Context Managers for Cleanup)

Jab dependency ko request complete hone ke baad cleanup ya connection close karna ho (e.g., DB session commit/rollback, third-party client close), `yield` syntax use hoti hai:

```python
from typing import AsyncGenerator
from fastapi import Depends

class MockDatabaseSession:
    def __init__(self):
        self.is_active = True

    async def commit(self):
        print("💾 Transaction committed.")

    async def rollback(self):
        print("⚠️ Transaction rolled back due to error.")

    async def close(self):
        self.is_active = False
        print("🔌 Database session closed.")

async def get_db_session() -> AsyncGenerator[MockDatabaseSession, None]:
    session = MockDatabaseSession()
    try:
        # Request execute hone se pehle yield hoga
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        # Request complete hone ke baad run hoga (guaranteed)
        await session.close()
```

### 2.2 Hierarchical (Sub-dependency) Trees

Dependencies doosri dependencies par rely kar sakti hain. FastAPI dependency tree solve karke automatically caching handle karta hai:

```python
from typing import Annotated
from fastapi import Depends, Header, HTTPException, status

def extract_api_key(x_api_key: Annotated[str | None, Header()] = None) -> str:
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Header 'X-API-Key' missing."
        )
    return x_api_key

def verify_tenant_access(
    api_key: Annotated[str, Depends(extract_api_key)]
) -> dict[str, str]:
    # Sub-dependency 'extract_api_key' pehle resolve hogi
    if api_key != "secret-master-token-123":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid tenant credentials."
        )
    return {"tenant_id": "org_9918", "tier": "enterprise"}
```

### 2.3 Class-Based Dependencies & Callable Objects

Stateful dependencies (jaise configurable pagination limits ya rate limiters) ke liye class-based callable objects ideal hain:

```python
from typing import Annotated
from fastapi import Depends, Query

class PaginationService:
    def __init__(self, max_limit: int = 50):
        self.max_limit = max_limit

    def __call__(
        self,
        page: Annotated[int, Query(ge=1)] = 1,
        limit: Annotated[int, Query(ge=1)] = 20
    ) -> dict[str, int]:
        actual_limit = min(limit, self.max_limit)
        return {
            "skip": (page - 1) * actual_limit,
            "limit": actual_limit,
            "page": page
        }

# Inject instances with custom configs
standard_pager = PaginationService(max_limit=50)
large_pager = PaginationService(max_limit=500)
```

---

## 3. Centralized Settings (`pydantic-settings`)

Production apps me configuration `.env` file se parse honi chahiye aur type-checked honi chahiye:

```python
# app/core/config.py
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    APP_NAME: str = "Enterprise Core API"
    ENVIRONMENT: str = Field(default="development", pattern=r"^(development|staging|production)$")
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str
    ALLOWED_ORIGINS: list[str] = ["http://localhost:3000"]
    DATABASE_URL: str

@lru_cache
def get_settings() -> AppSettings:
    """lru_cache ensure karta hai ki .env file baar baar disk se read na ho."""
    return AppSettings()
```

---

## 4. Layered Architecture: Separation of Concerns

Industry standard FastAPI codebase 4 distinct layers me divide hota hai:

```
Request ──▶ [Router / Controller]
                  │ (Extracts input & validates schema)
                  ▼
            [Service Layer]
                  │ (Business logic, calculations, rules)
                  ▼
            [Repository / DAO]
                  │ (Direct DB read/write queries)
                  ▼
            [Database / Storage]
```

### 4.1 Layer Responsibilities

1. **Router (`api/v1/endpoints/`)**:
   - HTTP routes define karta hai.
   - Pydantic models validate karta hai.
   - Status code aur response headers set karta hai.
   - *Rule:* Isme direct business calculations ya SQL queries kabhi nahi likhni chahiye.

2. **Service (`services/`)**:
   - Core business logic implement karta hai (e.g., invoice generation, password validation, order calculation).
   - Independent of HTTP protocol (unit testing me directly mock kiya ja sakta hai).

3. **Repository (`repositories/`)**:
   - Database operations (ORM queries, transactions, raw SQL) isolate karta hai.
   - Domain layer ko database engine swap karne me independence deta hai.

4. **Schemas (`schemas/`)**:
   - Request and response contract definitions (Pydantic V2).

---

## 5. Complete Layered Architecture Implementation

Yeh sample implementation dikhata hai ki kaise **Router**, **Service**, aur **Repository** `Depends()` ke through clean bind hote hain:

### 5.1 Repository Layer (`repositories/product_repo.py`)

```python
from uuid import UUID, uuid4
from decimal import Decimal
from pydantic import BaseModel

class ProductEntity(BaseModel):
    id: UUID
    title: str
    price: Decimal
    stock: int

class ProductRepository:
    """Mock Repository: Production me yahan SQLAlchemy ya raw SQL aayega."""
    def __init__(self):
        # In-memory storage table simulation
        self._table: dict[UUID, ProductEntity] = {}

    async def get_by_id(self, product_id: UUID) -> ProductEntity | None:
        return self._table.get(product_id)

    async def save(self, title: str, price: Decimal, stock: int) -> ProductEntity:
        entity = ProductEntity(
            id=uuid4(),
            title=title,
            price=price,
            stock=stock
        )
        self._table[entity.id] = entity
        return entity

    async def reduce_stock(self, product_id: UUID, qty: int) -> bool:
        entity = self._table.get(product_id)
        if not entity or entity.stock < qty:
            return False
        entity.stock -= qty
        return True

# Dependency provider for Repository
def get_product_repository() -> ProductRepository:
    return ProductRepository()
```

### 5.2 Service Layer (`services/product_service.py`)

```python
from uuid import UUID
from decimal import Decimal
from typing import Annotated
from fastapi import Depends, HTTPException, status
from repositories.product_repo import ProductRepository, get_product_repository

class ProductService:
    def __init__(
        self,
        repo: Annotated[ProductRepository, Depends(get_product_repository)]
    ):
        self.repo = repo

    async def create_new_product(self, title: str, price: Decimal, stock: int):
        # Business Rule 1: No zero-price luxury items
        if price <= Decimal("0.00"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Price must be strictly positive."
            )
        return await self.repo.save(title=title, price=price, stock=stock)

    async def purchase_product(self, product_id: UUID, quantity: int):
        product = await self.repo.get_by_id(product_id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found."
            )

        # Business Rule 2: Stock availability check
        success = await self.repo.reduce_stock(product_id, quantity)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Insufficient inventory. Available: {product.stock}"
            )

        total_price = product.price * Decimal(quantity)
        return {
            "product_id": product_id,
            "units_bought": quantity,
            "total_charged": total_price,
            "remaining_stock": product.stock
        }

# Dependency provider for Service
def get_product_service(
    service: Annotated[ProductService, Depends()]
) -> ProductService:
    return service
```

### 5.3 Router Layer (`api/v1/endpoints/products.py`)

```python
from typing import Annotated
from uuid import UUID
from decimal import Decimal
from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field

from services.product_service import ProductService, get_product_service

router = APIRouter(prefix="/products", tags=["Products"])

class ProductCreateDTO(BaseModel):
    title: str = Field(..., min_length=2, max_length=100)
    price: Decimal = Field(..., gt=Decimal("0.00"))
    stock: int = Field(..., ge=0)

class PurchaseDTO(BaseModel):
    quantity: int = Field(..., ge=1, le=50)

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_product(
    payload: ProductCreateDTO,
    service: Annotated[ProductService, Depends(get_product_service)]
):
    return await service.create_new_product(
        title=payload.title,
        price=payload.price,
        stock=payload.stock
    )

@router.post("/{product_id}/purchase", status_code=status.HTTP_200_OK)
async def buy_product(
    product_id: UUID,
    payload: PurchaseDTO,
    service: Annotated[ProductService, Depends(get_product_service)]
):
    return await service.purchase_product(
        product_id=product_id,
        quantity=payload.quantity
    )
```

---

## 6. Modular Project Structure (Phase 3 Standard)

```
app/
│
├── core/
│   ├── __init__.py
│   ├── config.py           # Pydantic BaseSettings & Environment
│   └── security.py         # Base hashing & cryptographic keys
│
├── api/
│   ├── __init__.py
│   └── v1/
│       ├── __init__.py
│       ├── router.py       # Aggregates all endpoint routers
│       └── endpoints/
│           ├── __init__.py
│           ├── products.py
│           └── users.py
│
├── schemas/                # Request & Response Contracts (Pydantic V2)
│   ├── __init__.py
│   ├── product.py
│   └── user.py
│
├── services/               # Pure Business Logic
│   ├── __init__.py
│   └── product_service.py
│
├── repositories/           # DB Abstraction Layer
│   ├── __init__.py
│   └── product_repo.py
│
├── models/                 # Database ORM entities (SQLAlchemy / Beanie)
│   └── __init__.py
│
└── main.py                 # App entrypoint & Lifespan
```

---

## 7. Phase 3 Mastery Checklist

- [ ] `Depends()` ka execution lifecycle samajh gaya?
- [ ] `yield` dependency ka use karke auto cleanup (commit/rollback) implement kar sakte hain?
- [ ] Sub-dependencies (dependency tree) chain karna aata hai?
- [ ] Configuration ke liye `pydantic-settings` ka structure clear hai?
- [ ] Layered architecture (Router → Service → Repository) ka rule pata hai ki router me direct business logic kyu nahi honi chahiye?