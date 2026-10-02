# FastAPI Phase 7 Developer Handbook: Testing, Structured Logging & Observability

Yeh handbook enterprise-grade FastAPI applications ko verify karne (**Pytest**, **HTTPX AsyncClient**, **Isolated Database Rollback Fixtures**, **Dependency Overrides**) aur production runtime par monitor karne (**Structured JSON Logging**, **Request Correlation IDs**, **Prometheus Metrics**, **Sentry/OpenTelemetry APM**) ka exhaustive reference guide hai.

---

## 1. Automated Async Testing Architecture

FastAPI ASGI applications ko test karne ke liye legacy `requests` ya `urllib` use nahi karna chahiye, kyunki wo synchronous blockings create karte hain. Production standard **`httpx.AsyncClient`** aur **`pytest-asyncio`** use karta hai.

### 1.1 Test Stack Standard
* **Test Runner**: `pytest`
* **Async Engine**: `pytest-asyncio`
* **ASGI Test Client**: `httpx.AsyncClient(transport=ASGITransport(app=app))`
* **Mocking & Isolation**: `unittest.mock`, `dependency_overrides`
* **Coverage Engine**: `pytest-cov`

---

## 2. Pytest Configuration & Test Database Fixtures

Har test case ke run hone ke baad database me dummy records nahi rehne chahiye. Best practice yeh hai ki har test execution ek isolated database transaction ke andar chale aur test end hone par **rollback** ho jaye.

### 2.1 `pytest.ini` Setup
```ini
# pytest.ini
[pytest]
asyncio_mode = auto
testpaths = tests
python_files = test_*.py
python_functions = test_*
addopts = -v -s --strict-markers --tb=short --cov=app --cov-report=term-missing
```

### 2.2 `conftest.py` (Test Fixture Engine)

```python
# tests/conftest.py
import asyncio
from typing import AsyncGenerator
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.main import app
from app.core.database import Base, get_db_session

# Dedicated isolated test database URL (SQLite in-memory or Test PostgreSQL)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)

@pytest.fixture(scope="session", autouse=True)
async def setup_test_db():
    """Session scope: Create all database tables once before test suite runs."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Function scope: Runs each test inside an isolated transaction and rolls back."""
    connection = await test_engine.connect()
    transaction = await connection.begin()
    session = TestSessionLocal(bind=connection)

    yield session

    await session.close()
    await transaction.rollback()
    await connection.close()

@pytest.fixture
async def async_client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Provides non-blocking HTTP client with overridden DB dependency."""
    # Override FastAPI DB dependency to use test session
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db_session] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client

    # Cleanup overrides after test completes
    app.dependency_overrides.clear()
```

---

## 3. Dependency Overrides & Auth Mocking

FastAPI ka `app.dependency_overrides` testing ka sabse powerful feature hai. Isse aap real external authentication, SMS gateways, ya Stripe payments ko test suite me easily mock kar sakte hain.

### 3.1 Mocking Authenticated User
```python
# tests/test_protected_routes.py
import pytest
from httpx import AsyncClient
from app.main import app
from app.core.dependencies import get_current_user, CurrentUserContext

@pytest.mark.asyncio
async def test_access_admin_portal_as_admin(async_client: AsyncClient):
    # Mocking authenticated admin user directly without generating JWT tokens
    def mock_admin_user():
        return CurrentUserContext(user_id="user-999", role="admin", jti="mock-jti-123")

    app.dependency_overrides[get_current_user] = mock_admin_user

    response = await async_client.get("/api/v1/vault/admin/inspect/1")
    
    assert response.status_code == 200
    assert response.json()["inspected_by"] == "user-999"

@pytest.mark.asyncio
async def test_access_admin_portal_unauthorized(async_client: AsyncClient):
    # Ensure real security fires when NO override or invalid token is supplied
    response = await async_client.get("/api/v1/vault/admin/inspect/1")
    assert response.status_code == 401
```

---

## 4. Structured JSON Logging & Request Tracing

Standard `print()` ya unstructured text logs production Kubernetes/Docker clusters me parse nahi ho pate. Industry standard **Structured JSON Logs** emit karta hai jisme har request ka **Unique Request ID (Correlation ID)** attach hota hai.

### 4.1 Correlation ID Middleware
```python
# app/core/middleware.py
import time
import uuid
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
import structlog

logger = structlog.get_logger()

class RequestTracingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Extract existing trace ID or generate a new UUID
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id

        # Bind context variable for this async task
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            client_ip=request.client.host if request.client else "unknown"
        )

        start_time = time.perf_counter()
        
        try:
            response = await call_next(request)
            process_time = (time.perf_counter() - start_time) * 1000
            
            logger.info(
                "http_request_finished",
                status_code=response.status_code,
                latency_ms=round(process_time, 2)
            )
            response.headers["X-Request-ID"] = request_id
            return response

        except Exception as exc:
            process_time = (time.perf_counter() - start_time) * 1000
            logger.error(
                "http_request_crashed",
                error=str(exc),
                latency_ms=round(process_time, 2)
            )
            raise
```

### 4.2 Structlog JSON Configuration
```python
# app/core/logging_config.py
import logging
import sys
import structlog

def setup_structured_logging():
    logging.basicConfig(format="%(message)s", stream=sys.stdout, level=logging.INFO)

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.dict_tracebacks,
            structlog.processors.JSONRenderer() # Emits pure JSON lines
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )
```

**Production Log Output Sample (JSON):**
```json
{
  "event": "http_request_finished",
  "level": "info",
  "timestamp": "2026-10-02T09:40:15.123456Z",
  "request_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
  "method": "POST",
  "path": "/api/v1/auth/login",
  "client_ip": "192.168.1.15",
  "status_code": 200,
  "latency_ms": 34.21
}
```

---

## 5. Production Observability: Metrics with Prometheus

APIs ki real-time health (RPS, Error Rate, 95th/99th Percentile Latency) track karne ke liye Prometheus middleware use hota hai.

```python
# app/core/telemetry.py
import time
from fastapi import FastAPI, Request
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response

# 1. Prometheus Metrics Definitions
HTTP_REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests handled by application",
    ["method", "endpoint", "status"]
)

HTTP_REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "HTTP request execution latency in seconds",
    ["method", "endpoint"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0]
)

def setup_metrics(app: FastAPI):
    @app.middleware("http")
    async def track_prometheus_metrics(request: Request, call_next):
        start_time = time.perf_counter()
        response = await call_next(request)
        latency = time.perf_counter() - start_time

        # Clean endpoint path template (e.g. /users/{id} instead of /users/123)
        endpoint = request.scope.get("route").path if request.scope.get("route") else request.url.path

        HTTP_REQUEST_COUNT.labels(
            method=request.method,
            endpoint=endpoint,
            status=response.status_code
        ).inc()

        HTTP_REQUEST_DURATION.labels(
            method=request.method,
            endpoint=endpoint
        ).observe(latency)

        return response

    # Expose scrape endpoint for Prometheus Server
    @app.get("/metrics", include_in_schema=False)
    def metrics():
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
```

---

## 6. Sentry Exception Tracking & APM

Unhandled 500 exceptions aur database bottleneck queries ko production me catch karne ke liye Sentry integrate kiya jata hai:

```python
# app/core/sentry.py
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

def init_sentry(dsn: str, environment: str = "production"):
    if not dsn:
        return

    sentry_sdk.init(
        dsn=dsn,
        environment=environment,
        integrations=[
            FastApiIntegration(transaction_style="endpoint"),
            SqlalchemyIntegration(),
        ],
        traces_sample_rate=0.2,       # 20% traces for performance tracking
        profiles_sample_rate=0.1,     # Profiling memory/CPU hot-paths
        send_default_pii=False        # Never leak passwords or sensitive tokens to Sentry!
    )
```

---

## 7. Execution Commands & Test Coverage

### Step 1: Install Testing & Observability Suite
```bash
pip install pytest pytest-asyncio httpx pytest-cov aiosqlite structlog prometheus-client sentry-sdk
```

### Step 2: Run Tests with Coverage Report
```bash
# Run all tests and enforce coverage threshold
pytest --cov=app --cov-report=term-missing --cov-fail-under=85
```

---

## 8. Phase 7 Mastery Checklist

* [ ] Kya tests me `ASGITransport` aur `httpx.AsyncClient` use ho raha hai bina live server start kiye?
* [ ] Kya tests ek isolated transaction ke andar chalte hain jo complete hone par **auto-rollback** ho jate hain?
* [ ] Kya `app.dependency_overrides` ka use karke external auth aur DB sessions clean mock ho rahe hain?
* [ ] Kya `structlog` standard JSON format emit kar raha hai jisme har request ka `request_id` tracked hai?
* [ ] Kya `/metrics` endpoint configure hai jo Prometheus counter aur latency histogram provide kar raha hai?
* [ ] Kya unhandled 500 exceptions me sensitive user credentials (PII) leak-safe tarike se log ho rahe hain?