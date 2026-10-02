# FastAPI Phase 4 Hands-On Industry Projects

Yeh document 2 production-grade database-driven projects provide karta hai jo strictly **Phase 4 (Async SQLAlchemy 2.0, PostgreSQL via asyncpg, Alembic Migrations, N+1 Prevention with selectinload, aur Redis Caching & Distributed Locking)** par based hain.

---

# Project 1: E-Commerce Catalog & Transactional Inventory Engine

### 1. Business Problem
Ek retail tech platform ko catalog aur inventory microservice develop karni hai:
* Categories aur Products ke beech 1-to-many relational hierarchy ho.
* Jab bhi category ke under products fetch kiye jayein, **N+1 query problem** na aaye (`selectinload` optimization mandatory).
* Product purchase/checkout ke waqt database level par **Atomic Transactional Rollback** support ho taaki stock negative na ho sake.
* Database schema versions ko **Alembic** se track aur migrate kiya jaye.

### 2. Architecture & File Structure

```
catalog_engine/
│
├── alembic/                    # Migration scripts
├── app/
│   ├── core/
│   │   ├── config.py           # Database URL & settings
│   │   └── database.py         # Async engine, sessionmaker & Base
│   ├── models/
│   │   └── catalog.py          # SQLAlchemy 2.0 Mapped entities
│   ├── schemas/
│   │   └── catalog_schema.py   # Pydantic V2 DTOs
│   ├── repositories/
│   │   └── catalog_repo.py     # Async ORM operations
│   ├── routers/
│   │   └── catalog_router.py   # FastAPI HTTP routes
│   └── main.py                 # ASGI application setup
├── alembic.ini
└── requirements.txt
```

### 3. Implementation Code

#### 3.1 `app/core/database.py`

```python
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

# Production PostgreSQL URL (asyncpg driver)
DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/catalog_db"

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)

class Base(DeclarativeBase):
    pass

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
```

#### 3.2 `app/models/catalog.py`

```python
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4
from sqlalchemy import ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

class Category(Base):
    __tablename__ = "categories"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(80), unique=True, index=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # 1-to-Many Relationship: Avoid N+1 via selectinload in queries
    products: Mapped[list["Product"]] = relationship(
        back_populates="category",
        cascade="all, delete-orphan",
        lazy="raise"  # Block sync access
    )

class Product(Base):
    __tablename__ = "products"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    category_id: Mapped[UUID] = mapped_column(ForeignKey("categories.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(150), index=True, nullable=False)
    sku: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    stock: Mapped[int] = mapped_column(default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))

    category: Mapped["Category"] = relationship(back_populates="products")
```

#### 3.3 `app/schemas/catalog_schema.py`

```python
from decimal import Decimal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field

class CategoryCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=80)
    slug: str = Field(..., pattern=r"^[a-z0-9-]+$")
    description: str | None = None

class ProductCreate(BaseModel):
    category_id: UUID
    title: str = Field(..., min_length=2, max_length=150)
    sku: str = Field(..., pattern=r"^[A-Z0-9_-]+$")
    price: Decimal = Field(..., gt=Decimal("0.00"))
    stock: int = Field(..., ge=0)

class ProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    sku: str
    price: Decimal
    stock: int

class CategoryWithProductsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    slug: str
    products: list[ProductResponse] = []
```

#### 3.4 `app/repositories/catalog_repo.py`

```python
from uuid import UUID
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.catalog import Category, Product

class CatalogRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_category(self, name: str, slug: str, description: str | None) -> Category:
        category = Category(name=name, slug=slug, description=description)
        self.session.add(category)
        await self.session.flush()
        await self.session.refresh(category)
        return category

    async def create_product(self, data: dict) -> Product:
        product = Product(**data)
        self.session.add(product)
        await self.session.flush()
        await self.session.refresh(product)
        return product

    async def get_category_with_products(self, category_id: UUID) -> Category | None:
        """Solves N+1 using selectinload."""
        stmt = (
            select(Category)
            .options(selectinload(Category.products))
            .where(Category.id == category_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def reduce_product_stock(self, product_id: UUID, qty: int) -> bool:
        """Atomic stock deduction."""
        stmt = (
            update(Product)
            .where(Product.id == product_id, Product.stock >= qty)
            .values(stock=Product.stock - qty)
        )
        result = await self.session.execute(stmt)
        return result.rowcount > 0
```

#### 3.5 `app/routers/catalog_router.py` & `main.py`

```python
# app/routers/catalog_router.py
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db_session
from app.repositories.catalog_repo import CatalogRepository
from app.schemas.catalog_schema import (
    CategoryCreate,
    CategoryWithProductsResponse,
    ProductCreate,
    ProductResponse
)

router = APIRouter(prefix="/catalog", tags=["Catalog Management"])

@router.post("/categories", response_model=CategoryWithProductsResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    payload: CategoryCreate,
    session: AsyncSession = Depends(get_db_session)
):
    repo = CatalogRepository(session)
    return await repo.create_category(payload.name, payload.slug, payload.description)

@router.post("/products", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    payload: ProductCreate,
    session: AsyncSession = Depends(get_db_session)
):
    repo = CatalogRepository(session)
    return await repo.create_product(payload.model_dump())

@router.get("/categories/{category_id}", response_model=CategoryWithProductsResponse)
async def get_category_details(
    category_id: UUID,
    session: AsyncSession = Depends(get_db_session)
):
    repo = CatalogRepository(session)
    category = await repo.get_category_with_products(category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category

@router.post("/products/{product_id}/checkout")
async def checkout_product(
    product_id: UUID,
    units: int = 1,
    session: AsyncSession = Depends(get_db_session)
):
    repo = CatalogRepository(session)
    deducted = await repo.reduce_product_stock(product_id, units)
    if not deducted:
        raise HTTPException(status_code=409, detail="Insufficient stock or invalid product ID")
    return {"status": "success", "message": f"{units} units reserved successfully."}

# app/main.py
from fastapi import FastAPI
from app.routers.catalog_router import router as catalog_router

app = FastAPI(title="Async Catalog & Inventory API", version="1.0.0")
app.include_router(catalog_router)
```

---

# Project 2: High-Throughput Redis Cache-Aside & Distributed Lock Service

### 1. Business Problem
E-Commerce flash sale events par ek sath 10,000+ users aate hain:
* Bar-bar PostgreSQL database query hit karne se database choke ho jata hai. Isliye **Cache-Aside Pattern** implement karna hai (Agar Redis me cache ho toh 2ms me return ho, warna DB se load hokar 5 minute ke liye Redis me cache ho).
* Jab seller product update kare, toh purana cache **Invalidate / Purge** hona chahiye.
* Multiple concurrent checkouts ke waqt overselling se bachne ke liye **Redis Distributed Lock** pattern use ho.

### 2. Implementation Code

```python
import json
import asyncio
from uuid import UUID, uuid4
from typing import AsyncGenerator
from fastapi import FastAPI, Depends, HTTPException, status
from pydantic import BaseModel
import redis.asyncio as aioredis

app = FastAPI(title="Redis Flash Sale & Caching Layer")

# ----------------------------------------------------
# 1. Redis Connection Pool
# ----------------------------------------------------
redis_pool = aioredis.ConnectionPool.from_url(
    "redis://localhost:6379/0",
    decode_responses=True,
    max_connections=20
)

async def get_redis() -> AsyncGenerator[aioredis.Redis, None]:
    client = aioredis.Redis(connection_pool=redis_pool)
    try:
        yield client
    finally:
        await client.close()

# ----------------------------------------------------
# 2. Simulated Primary Database Store
# ----------------------------------------------------
DB_PRODUCTS: dict[str, dict] = {
    "prod_101": {"id": "prod_101", "name": "Flagship Smartphone", "price": 49999.00, "stock": 5},
    "prod_102": {"id": "prod_102", "name": "Wireless ANC Earbuds", "price": 8999.00, "stock": 50},
}

class ProductUpdateDTO(BaseModel):
    price: float
    stock: int

# ----------------------------------------------------
# 3. Cache-Aside Lookup Endpoint
# ----------------------------------------------------
@app.get("/api/v1/products/{product_id}")
async def get_product(
    product_id: str,
    redis: aioredis.Redis = Depends(get_redis)
):
    cache_key = f"cache:product:{product_id}"

    # Step 1: Check Redis
    cached = await redis.get(cache_key)
    if cached:
        return {"source": "REDIS_CACHE", "data": json.loads(cached)}

    # Step 2: Cache Miss -> Read Primary DB
    product = DB_PRODUCTS.get(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Step 3: Write back to Redis with 180s TTL (3 mins)
    await redis.setex(cache_key, 180, json.dumps(product))
    return {"source": "PRIMARY_DATABASE", "data": product}

# ----------------------------------------------------
# 4. Cache Invalidation on Update
# ----------------------------------------------------
@app.put("/api/v1/products/{product_id}")
async def update_product(
    product_id: str,
    payload: ProductUpdateDTO,
    redis: aioredis.Redis = Depends(get_redis)
):
    if product_id not in DB_PRODUCTS:
        raise HTTPException(status_code=404, detail="Product not found")

    # 1. Update Primary DB
    DB_PRODUCTS[product_id]["price"] = payload.price
    DB_PRODUCTS[product_id]["stock"] = payload.stock

    # 2. Cache Invalidation (Eviction)
    cache_key = f"cache:product:{product_id}"
    await redis.delete(cache_key)

    return {"message": "Product updated and Redis cache evicted successfully."}

# ----------------------------------------------------
# 5. Distributed Locking for Flash Sale Checkouts
# ----------------------------------------------------
@app.post("/api/v1/products/{product_id}/flash-buy")
async def flash_sale_purchase(
    product_id: str,
    redis: aioredis.Redis = Depends(get_redis)
):
    lock_key = f"lock:product:{product_id}"
    lock_token = str(uuid4())

    # Acquire distributed lock with 5-second automatic timeout (avoids deadlock)
    acquired = await redis.set(lock_key, lock_token, nx=True, ex=5)
    if not acquired:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="High traffic surge! Another transaction is reserving this product. Retry shortly."
        )

    try:
        # Critical Section (Protected by lock)
        product = DB_PRODUCTS.get(product_id)
        if not product or product["stock"] <= 0:
            raise HTTPException(status_code=409, detail="Sold out!")

        # Simulating processing / external payment gateway latency
        await asyncio.sleep(0.05)
        product["stock"] -= 1

        # Evict cache to reflect fresh stock count
        await redis.delete(f"cache:product:{product_id}")

        return {
            "status": "SUCCESS",
            "message": f"Successfully purchased 1 unit of {product['name']}.",
            "remaining_stock": product["stock"]
        }
    finally:
        # Safe release: Release lock ONLY if the value matches our token
        current_lock_val = await redis.get(lock_key)
        if current_lock_val == lock_token:
            await redis.delete(lock_key)
```

---

## 4. How to Setup, Migrate & Verify

### Step 1: Install Dependencies
```bash
pip install fastapi uvicorn[standard] sqlalchemy[asyncio] asyncpg alembic redis pydantic
```

### Step 2: Alembic Migrations Setup (Project 1)
```bash
# Initialize alembic async template
alembic init -t async alembic

# env.py me Base.metadata bind karein aur run karein:
alembic revision --autogenerate -m "create_catalog_tables"
alembic upgrade head
```

### Step 3: Run Redis & Test Caching (Project 2)
```bash
# Redis server start karein
redis-server

# App start karein
uvicorn app.main:app --reload --port 8000
```

1. **Verify Cache-Aside**:
   * Pehli baar `GET /api/v1/products/prod_101` call karein $\rightarrow$ `source: PRIMARY_DATABASE`.
   * Turant doosri baar call karein $\rightarrow$ `source: REDIS_CACHE` (0ms-2ms response time).
2. **Verify Cache Eviction**:
   * `PUT /api/v1/products/prod_101` call karke price update karein.
   * Agli GET call dubara `PRIMARY_DATABASE` se hogi aur updated data cache me daal degi.
3. **Verify Distributed Lock**:
   * Ek sath 10 simultaneous requests bhej kar check karein ki stock exact decrease ho raha hai aur koi overselling nahi ho rahi.