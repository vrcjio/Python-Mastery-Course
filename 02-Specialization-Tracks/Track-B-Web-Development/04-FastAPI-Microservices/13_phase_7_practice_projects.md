# FastAPI Phase 7 Hands-On Industry Projects

Yeh document 2 production-grade testing aur observability projects provide karta hai jo strictly **Phase 7 (Pytest Async Engine, Transactional DB Rollback Fixtures, Dependency Overrides, Structured JSON Logging, Request Correlation IDs, aur Prometheus Metrics Exporter)** par based hain.

---

# Project 1: Production-Ready Async Test Harness & CI Verification Engine

### 1. Problem Statement
Production FastAPI apps me real database par tests chalana risky hota hai (data pollution aur race conditions hoti hain). Hamen ek automated testing pipeline construct karni hai jo:
* Bina actual live server spin kiye pure ASGI level par async HTTP requests execute kare (`httpx.AsyncClient`).
* In-memory async SQLite engine use kare jo tests shuru hone se pehle schemas create kare aur end hone par clean kare.
* Har test method ke liye **Isolated Transactional Rollback** provide kare (test ke andar insert kiya hua record test khatam hote hi database se gayab ho jaye).
* RBAC auth tokens ko har bar generate karne ke bajaye `app.dependency_overrides` se safely mock kare.
* Coverage report enforce kare ($\ge 85\%$).

### 2. Architecture & File Structure

```
test_harness_engine/
│
├── app/
│   ├── core/
│   │   ├── config.py
│   │   ├── database.py         # Primary SQLAlchemy async engine & Base
│   │   └── security.py         # Token validator & CurrentUser dependency
│   ├── models/
│   │   └── account.py          # SQLAlchemy 2.0 Account entity
│   ├── routers/
│   │   └── account_router.py   # CRUD Endpoints
│   └── main.py
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py             # Fixtures: In-memory DB, Rollback engine, AsyncClient
│   └── test_accounts.py        # Integration test cases
│
├── pytest.ini                  # Pytest configuration & coverage thresholds
└── requirements.txt
```

### 3. Implementation Code

#### 3.1 `app/models/account.py` & `app/core/database.py`

```python
# app/core/database.py
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/primary_db"

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session

# app/models/account.py
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4
from sqlalchemy import Numeric, String
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base

class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    email: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    account_number: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    balance: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
```

#### 3.2 `app/routers/account_router.py` & `app/main.py`

```python
# app/routers/account_router.py
from decimal import Decimal
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db_session
from app.models.account import Account

router = APIRouter(prefix="/api/v1/accounts", tags=["Bank Accounts"])

class AccountCreateDTO(BaseModel):
    email: EmailStr
    account_number: str = Field(..., pattern=r"^ACC-\d{6}$")
    initial_deposit: Decimal = Field(..., ge=Decimal("100.00"))

class AccountResponseDTO(BaseModel):
    id: UUID
    email: EmailStr
    account_number: str
    balance: Decimal
    is_active: bool

    class Config:
        from_attributes = True

# Security context dummy
async def verify_auth_principal() -> dict:
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Bearer token required")

@router.post("/", response_model=AccountResponseDTO, status_code=status.HTTP_201_CREATED)
async def open_account(
    payload: AccountCreateDTO,
    session: AsyncSession = Depends(get_db_session),
    user: dict = Depends(verify_auth_principal)
):
    # Check duplicate
    stmt = select(Account).where(Account.email == payload.email)
    existing = (await session.execute(stmt)).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Account with this email already exists.")

    new_acc = Account(
        email=payload.email,
        account_number=payload.account_number,
        balance=payload.initial_deposit
    )
    session.add(new_acc)
    await session.commit()
    await session.refresh(new_acc)
    return new_acc

@router.get("/{account_id}", response_model=AccountResponseDTO)
async def get_account_by_id(
    account_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    user: dict = Depends(verify_auth_principal)
):
    stmt = select(Account).where(Account.id == account_id)
    acc = (await session.execute(stmt)).scalar_one_or_none()
    if not acc:
        raise HTTPException(status_code=404, detail="Account record not found.")
    return acc

# app/main.py
from fastapi import FastAPI
from app.routers.account_router import router as account_router

app = FastAPI(title="Core Banking Microservice")
app.include_router(account_router)
```

#### 3.3 `tests/conftest.py` (The Isolated Transaction Engine)

```python
import asyncio
from typing import AsyncGenerator
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.main import app
from app.core.database import Base, get_db_session
from app.routers.account_router import verify_auth_principal

# Isolated In-Memory SQLite Async Database for testing
TEST_DB_URL = "sqlite+aiosqlite:///:memory:"
test_engine = create_async_engine(TEST_DB_URL, echo=False)
TestSessionLocal = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)

@pytest_asyncio.fixture(scope="session", autouse=True)
async def prepare_database_schema():
    """Build schemas once before test suite starts, drop when finished."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    CRITICAL FIXTURE:
    Binds an external connection and begins a sub-transaction.
    Tests operate inside this transaction and it rolls back on test teardown.
    """
    connection = await test_engine.connect()
    transaction = await connection.begin()
    session = TestSessionLocal(bind=connection)

    yield session

    await session.close()
    await transaction.rollback()
    await connection.close()

@pytest_asyncio.fixture
async def authenticated_client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Overrides DB session with isolated rollback fixture and injects mock auth context."""
    async def override_db():
        yield db_session

    async def override_auth():
        return {"sub": "staff_auditor_01", "role": "ADMIN"}

    app.dependency_overrides[get_db_session] = override_db
    app.dependency_overrides[verify_auth_principal] = override_auth

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client

    app.dependency_overrides.clear()
```

#### 3.4 `tests/test_accounts.py` (Test Cases)

```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_create_account_success(authenticated_client: AsyncClient):
    payload = {
        "email": "customer1@test.com",
        "account_number": "ACC-123456",
        "initial_deposit": "5000.00"
    }
    response = await authenticated_client.post("/api/v1/accounts/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "customer1@test.com"
    assert data["balance"] == "5000.00"
    assert "id" in data

@pytest.mark.asyncio
async def test_create_account_duplicate_rejection(authenticated_client: AsyncClient):
    payload = {
        "email": "duplicate@test.com",
        "account_number": "ACC-999999",
        "initial_deposit": "1000.00"
    }
    # First creation passes
    r1 = await authenticated_client.post("/api/v1/accounts/", json=payload)
    assert r1.status_code == 201

    # Second creation fails with 400
    r2 = await authenticated_client.post("/api/v1/accounts/", json=payload)
    assert r2.status_code == 400
    assert "already exists" in r2.json()["detail"]

@pytest.mark.asyncio
async def test_rollback_isolation_guarantee(authenticated_client: AsyncClient):
    """
    Even though previous tests created accounts, they rolled back!
    The database should not have 'customer1@test.com' persisted.
    """
    payload = {
        "email": "customer1@test.com", # Reusing same email from test 1
        "account_number": "ACC-123456",
        "initial_deposit": "200.00"
    }
    # If rollback worked, this will return 201, NOT 400!
    response = await authenticated_client.post("/api/v1/accounts/", json=payload)
    assert response.status_code == 201
```

---

# Project 2: Enterprise Observability & Tracing Gateway

### 1. Problem Statement
High-scale production APIs me plain console logs search karna impossible hota hai. Hamen ek standard Observability Layer design karni hai:
* **Unique Correlation ID**: Har request me incoming `X-Request-ID` extract ho, ya UUIDv4 generate ho kar request state aur response header me pass ho.
* **Structured JSON Logging (`structlog`)**: Har log line pure JSON ho jisme timestamp, log level, request path, method, status code, aur client IP strictly binded hon. Passwords ya bearer tokens logs me leak na hon.
* **Prometheus Metrics Exporter**: Real-time traffic, HTTP counters (split by route, status code), aur latency histogram bucket expose kare on `/metrics`.
* **Error Rate Alerts Tracker**: Global exception interceptor jo unhandled 500 runtime errors ko standard JSON envelope me deliver kare bina internal stacktraces expose kiye.

### 2. Architecture & File Structure

```
observability_gateway/
│
├── app/
│   ├── core/
│   │   ├── logging.py          # Structlog JSON configuration
│   │   ├── middleware.py       # Correlation ID & Prometheus Timing Middleware
│   │   └── metrics.py          # Prometheus Counter & Histogram registry
│   ├── routers/
│   │   └── business.py         # Sample business routes with simulated latency
│   └── main.py
│
└── requirements.txt
```

### 3. Implementation Code

#### 3.1 `app/core/logging.py` & `app/core/metrics.py`

```python
# app/core/logging.py
import logging
import sys
import structlog

def setup_structured_logging():
    logging.basicConfig(format="%(message)s", stream=sys.stdout, level=logging.INFO)

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer() # Pure machine-readable JSON
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

# app/core/metrics.py
from prometheus_client import Counter, Histogram

REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP Requests",
    ["method", "endpoint", "http_status"]
)

REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP Request Latency in seconds",
    ["method", "endpoint"],
    buckets=[0.005, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5]
)
```

#### 3.2 `app/core/middleware.py` (Correlation ID & Metric Interceptor)

```python
import time
import uuid
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
import structlog
from app.core.metrics import REQUEST_COUNT, REQUEST_LATENCY

logger = structlog.get_logger()

class ObservabilityMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # 1. Correlation ID Resolution
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
        request.state.correlation_id = correlation_id

        # 2. Context binding for all downstream logs in this coroutine
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            correlation_id=correlation_id,
            http_method=request.method,
            http_path=request.url.path,
            remote_ip=request.client.host if request.client else "unknown"
        )

        start_time = time.perf_counter()
        route_template = request.url.path  # fallback

        try:
            response = await call_next(request)
            duration = time.perf_counter() - start_time

            # Normalize route name from matched router scope
            if request.scope.get("route"):
                route_template = request.scope["route"].path

            # 3. Prometheus Metric Recording
            REQUEST_COUNT.labels(
                method=request.method,
                endpoint=route_template,
                http_status=response.status_code
            ).inc()

            REQUEST_LATENCY.labels(
                method=request.method,
                endpoint=route_template
            ).observe(duration)

            # 4. Structured Request Completion Log
            logger.info(
                "request_processed",
                status_code=response.status_code,
                latency_ms=round(duration * 1000, 2)
            )

            response.headers["X-Correlation-ID"] = correlation_id
            return response

        except Exception as exc:
            duration = time.perf_counter() - start_time
            REQUEST_COUNT.labels(
                method=request.method,
                endpoint=route_template,
                http_status=500
            ).inc()

            logger.error(
                "request_failed",
                error=str(exc),
                latency_ms=round(duration * 1000, 2)
            )
            raise
```

#### 3.3 `app/main.py` (App Assembly & Metrics Scraping Endpoint)

```python
import asyncio
import random
from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
import structlog

from app.core.logging import setup_structured_logging
from app.core.middleware import ObservabilityMiddleware

setup_structured_logging()
logger = structlog.get_logger()

app = FastAPI(title="Observability Core Gateway", version="1.0.0")
app.add_middleware(ObservabilityMiddleware)

# Prometheus Scrape Target
@app.get("/metrics", include_in_schema=False)
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

# Business Routes
@app.get("/api/v1/payments/process")
async def process_simulated_payment():
    # Simulate jitter latency
    latency = random.uniform(0.02, 0.25)
    await asyncio.sleep(latency)

    logger.info("payment_gateway_contacted", provider="STRIPE", latency_sim=latency)
    return {"status": "PAYMENT_SETTLED", "currency": "INR", "amount": 1499.00}

@app.get("/api/v1/payments/fault")
async def trigger_fault():
    logger.warn("unstable_downstream_service_accessed")
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Downstream payment clearing network unreachable."
    )
```

---

## 4. How to Run & Verify Phase 7 Projects

### Step 1: Install Dependencies
```bash
pip install fastapi uvicorn[standard] pytest pytest-asyncio pytest-cov httpx aiosqlite sqlalchemy structlog prometheus-client
```

### Step 2: Running Automated Tests (Project 1)
In the project directory:
```bash
pytest -v --cov=app --cov-report=term-missing
```
* Observe that tests pass asynchronously without starting any background Uvicorn server.
* Observe that `test_rollback_isolation_guarantee` succeeds with status `201`, proving that prior tests left zero dirty records behind in the database.

### Step 3: Running & Observing Live Logs & Metrics (Project 2)
Start the application:
```bash
uvicorn app.main:app --reload --port 8000
```

1. **Test Normal Request with Structured Log**:
   Send a request via curl:
   ```bash
   curl -i http://localhost:8000/api/v1/payments/process
   ```
   * Inspect the response header: `X-Correlation-ID: <uuid>` is present.
   * Inspect the terminal output: Notice pure, single-line JSON with `correlation_id`, `latency_ms`, and `status_code: 200`.

2. **Check Prometheus Metrics**:
   Open in your browser:
   ```
   http://localhost:8000/metrics
   ```
   * Search for `http_requests_total` and `http_request_duration_seconds_bucket`.
   * You will see real-time counters and latency distributions ready to be scraped by Prometheus and Grafana dashboards.