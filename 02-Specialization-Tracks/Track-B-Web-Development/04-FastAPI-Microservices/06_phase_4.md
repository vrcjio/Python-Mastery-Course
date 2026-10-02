# FastAPI Phase 4 Developer Handbook: Database Integration, Async ORM & Caching

Yeh handbook FastAPI me modern relational database handling (**SQLAlchemy 2.0 Async**, **Alembic**, **PostgreSQL via asyncpg**) aur in-memory high-speed caching (**Redis**) ke enterprise architecture aur best practices ka detailed reference guide hai.

---

## 1. Async Database Architecture & Core Concepts

FastAPI ke asynchronous I/O ka pura fayda lene ke liye database driver aur ORM dono ka **non-blocking** hona mandatory hai. Traditional synchronous drivers (jaise `psycopg2`, sync SQLite) ASGI event loop ko freeze kar dete hain.

### 1.1 Tech Stack Standard
* **Driver**: `asyncpg` (PostgreSQL ke liye ultra-fast async driver)
* **ORM Engine**: `SQLAlchemy 2.0+` (Type-safe declarative mapping)
* **Migrations**: `Alembic` (Async context supported)
* **In-Memory Cache & Distributed Lock**: `redis-py` (asyncio mode)

---

## 2. SQLAlchemy 2.0 Modern Setup (Engine & Sessions)

SQLAlchemy 2.0 me purana `sessionmaker` pattern deprecate ho chuka hai. Ab `create_async_engine` aur `async_sessionmaker` use hota hai:

```python
# app/core/database.py
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

# Production URL Format: postgresql+asyncpg://user:password@host:port/dbname
DATABASE_URL = "postgresql+asyncpg://postgres:secretpassword@localhost:5432/fastapi_db"

# 1. Async Engine Creation with Connection Pooling
engine = create_async_engine(
    DATABASE_URL,
    echo=False,              # Set True only for local SQL debug
    pool_size=10,           # Persistent connections in pool
    max_overflow=20,        # Temporary connections under high traffic
    pool_recycle=3600,      # Recycle connections hourly to prevent stale timeouts
    pool_pre_ping=True      # Check connection health before checking out
)

# 2. Async Session Factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Attributes commit hone ke baad reload na hon (Async me critical!)
    autoflush=False
)

# 3. Base Class for ORM Entities
class Base(DeclarativeBase):
    pass

# 4. Dependency Injection Provider (Yield Context)
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provides a transactional database session per request with guaranteed cleanup."""
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

---

## 3. Modern Declarative Models (SQLAlchemy 2.0 Type-Safe Mappings)

SQLAlchemy 2.0 me `Column(...)` ki jagah `Mapped[type]` aur `mapped_column(...)` use hota hai, jo Python type hinting aur IDE autocompletion ke sath integrate hota hai:

```python
# app/models/entities.py
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4
from sqlalchemy import ForeignKey, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

class User(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))

    # 1-to-Many Relationship
    orders: Mapped[list["Order"]] = relationship(
        back_populates="customer",
        cascade="all, delete-orphan",
        lazy="raise"  # Accidentally sync access karne par error throw karega!
    )

class Order(Base):
    __tablename__ = "orders"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    order_number: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    customer_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="PENDING")
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))

    # Relationship Backref
    customer: Mapped["User"] = relationship(back_populates="orders")
```

---

## 4. Querying & The N+1 Problem (Eager vs Lazy Loading)

### 4.1 Kyu hota hai N+1 Problem?
Agar aap 10 orders fetch karte hain aur har order ke user ka email access karte hain, toh agar relationship lazy hai:
* 1 Query chalegi 10 orders fetch karne ke liye.
* Fir 10 alag queries chalegi har order ke user ko fetch karne ke liye ($1 + 10 = 11$ DB calls).
Yeh high-traffic me database ko choke kar deta hai.

### 4.2 Async Solution: `selectinload` vs `joinedload`
* **`selectinload`**: 1-to-Many ya Many-to-Many collections load karne ke liye best hota hai (2 queries me saara data IN clause se le aata hai).
* **`joinedload`**: Many-to-1 relationships (Foreign Key parent record) ke liye best hota hai (Single SQL JOIN karta hai).

```python
from sqlalchemy import select
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.ext.asyncio import AsyncSession

# Eager Loading 1-to-Many without N+1 issue
async def get_user_with_all_orders(session: AsyncSession, user_id: UUID) -> User | None:
    query = (
        select(User)
        .options(selectinload(User.orders))
        .where(User.id == user_id)
    )
    result = await session.execute(query)
    return result.scalar_one_or_none()

# Eager Loading Many-to-1 with Single JOIN
async def get_order_with_customer(session: AsyncSession, order_id: UUID) -> Order | None:
    query = (
        select(Order)
        .options(joinedload(Order.customer))
        .where(Order.id == order_id)
    )
    result = await session.execute(query)
    return result.scalar_one_or_none()
```

---

## 5. Async CRUD Repository Pattern

Production me direct session calls routes me likhne ke bajaye ek dedicated repository layer banani chahiye:

```python
# app/repositories/user_repo.py
from uuid import UUID
from typing import Sequence
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.entities import User

class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, user_id: UUID) -> User | None:
        query = select(User).where(User.id == user_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        query = select(User).where(User.email == email)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def list_users(self, limit: int = 20, offset: int = 0) -> Sequence[User]:
        query = select(User).offset(offset).limit(limit).order_by(User.created_at.desc())
        result = await self.session.execute(query)
        return result.scalars().all()

    async def create(self, username: str, email: str, hashed_pw: str) -> User:
        new_user = User(
            username=username,
            email=email,
            hashed_password=hashed_pw
        )
        self.session.add(new_user)
        await self.session.flush()  # DB me push karta hai bina commit kiye taaki UUID generate ho jaye
        await self.session.refresh(new_user)
        return new_user

    async def deactivate(self, user_id: UUID) -> bool:
        stmt = (
            update(User)
            .where(User.id == user_id)
            .values(is_active=False)
        )
        result = await self.session.execute(stmt)
        return result.rowcount > 0
```

---

## 6. Database Migrations using Alembic (Async Setup)

Alembic database schema versions ko track karne aur auto-generate karne ka standard tool hai.

### 6.1 Installation & Initialization
```bash
pip install alembic asyncpg psycopg2-binary
alembic init -t async migrations
```
*(Yahan `-t async` template asyncpg driver support ke liye zaroori hai)*

### 6.2 `migrations/env.py` Configuration
`migrations/env.py` me apne models ki `Base.metadata` bind karni hoti hai:

```python
# migrations/env.py me import karein:
from app.core.database import Base
from app.models.entities import User, Order  # Saare models import karein taaki Alembic detect kare

# Set target metadata:
target_metadata = Base.metadata
```

### 6.3 Standard Migration Commands
```bash
# 1. Nayi migration file generate karein (Auto-detection)
alembic revision --autogenerate -m "create_users_and_orders_table"

# 2. Database me migration apply karein
alembic upgrade head

# 3. Agar koi issue ho toh pichle version par rollback karein
alembic downgrade -1
```

---

## 7. Redis Integration (Caching & Distributed Rate Limiting)

Redis database load ko kam karne ke liye high-speed in-memory layer provide karta hai.

### 7.1 Async Redis Connection Provider
```python
# app/core/redis.py
from typing import AsyncGenerator
import redis.asyncio as aioredis

REDIS_URL = "redis://localhost:6379/0"

# Redis client pool
redis_pool = aioredis.ConnectionPool.from_url(
    REDIS_URL,
    max_connections=20,
    decode_responses=True  # Automatically bytes ko UTF-8 string me convert karta hai
)

async def get_redis_client() -> AsyncGenerator[aioredis.Redis, None]:
    client = aioredis.Redis(connection_pool=redis_pool)
    try:
        yield client
    finally:
        await client.close()
```

### 7.2 Cache-Aside Pattern Implementation
Agar record Redis me mil jaye toh DB hit na ho; agar na mile toh DB se fetch karke Redis me TTL (Time To Live) ke sath cache ho:

```python
import json
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as aioredis

from app.core.database import get_db_session
from app.core.redis import get_redis_client
from app.repositories.user_repo import UserRepository

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/{user_id}")
async def get_user_profile(
    user_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    redis: aioredis.Redis = Depends(get_redis_client)
):
    cache_key = f"user_cache:{user_id}"

    # 1. Check Redis Cache First
    cached_data = await redis.get(cache_key)
    if cached_data:
        return {"source": "cache", "data": json.loads(cached_data)}

    # 2. Cache Miss: Fetch from PostgreSQL
    repo = UserRepository(session)
    user = await repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    user_payload = {
        "id": str(user.id),
        "username": user.username,
        "email": user.email,
        "is_active": user.is_active
    }

    # 3. Store in Redis with 300 seconds TTL (5 minutes expiry)
    await redis.setex(cache_key, 300, json.dumps(user_payload))

    return {"source": "database", "data": user_payload}
```

---

## 8. Phase 4 Production Checklist

- [ ] Kya engine me `create_async_engine` aur async driver (`postgresql+asyncpg`) use ho raha hai?
- [ ] Kya `expire_on_commit=False` set hai `async_sessionmaker` me?
- [ ] Kya relationships me `lazy="raise"` configure kiya hai taaki runtime par synchronous N+1 queries na trigger hon?
- [ ] Kya 1-to-many collections ke liye `selectinload` use ho raha hai?
- [ ] Kya schema changes ke liye Alembic migrations auto-generate aur upgrade command check ki gayi hai?
- [ ] Kya Redis queries me keys ka standard prefix (e.g., `user:101`) aur appropriate TTL expiry set kiya hai?