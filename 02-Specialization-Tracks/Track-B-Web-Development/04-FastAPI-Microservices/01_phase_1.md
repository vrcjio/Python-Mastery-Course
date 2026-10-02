# FastAPI Phase 1 Developer Handbook: Modern Concurrency & Core API Foundations

Yeh document Phase 1 ke sabhi fundamental aur internal concepts ka detailed, production-focused reference guide hai. Iska use aap self-study notes aur production project architecture set karne ke liye kar sakte hain.

---

## 1. Modern Python Typing & Type Hinting

FastAPI ka internal serialization, validation (via Pydantic), aur OpenAPI documentation generation puri tarah Python type hints par based hai.

### 1.1 Core Typing Constructs

```python
from typing import (
    Annotated,
    Any,
    Dict,
    List,
    Literal,
    Optional,
    Tuple,
    TypeAlias,
    Union,
)

# Union vs Pipe operator (Python 3.10+)
# Purana tarika: Union[str, int]
# Modern tarika:
UserID: TypeAlias = int | str

# Optional (Same as: str | None)
Username: TypeAlias = str | None

# Literal: Sirf strictly specified constant values accept karta hai
UserRole = Literal["superadmin", "tenant_admin", "staff", "customer"]

# Collections
MetadataDict: TypeAlias = dict[str, Any]
CoordList: TypeAlias = list[tuple[float, float]]


def evaluate_access(role: UserRole, user_id: UserID) -> bool:
    if role == "superadmin":
        return True
    return False
```

### 1.2 `typing.Annotated` Pattern
`Annotated` FastAPI me metadata aur dependency injection inject karne ka standard tarika hai. Isse type definition aur business logic validate karne wale metadata separate rehte hain.

```python
from typing import Annotated
from fastapi import Path, Query

# Annotated[<BaseType>, <FastAPI_Metadata_or_Dependency>]
StrictAge = Annotated[
    int, 
    Path(..., ge=18, le=120, description="Age must be between 18 and 120 years")
]

SearchFilter = Annotated[
    str | None, 
    Query(max_length=50, regex=r"^[a-zA-Z0-9_-]+$", description="Alphanumeric search term")
]
```

---

## 2. Concurrency, Asyncio & ASGI Mechanics

### 2.1 ASGI vs WSGI Architecture
* **WSGI (Web Server Gateway Interface)**:
  * Synchronous model (Flask, Django default).
  * Har request ek dedicated thread/process block karti hai.
  * Concurrency limit OS threads ki limit par rely karti hai.
* **ASGI (Asynchronous Server Gateway Interface)**:
  * Asynchronous model (FastAPI, Starlette, Quart).
  * Single thread event loop hazaron concurrent I/O connections handle karta hai non-blocking tarike se.
  * ASGI Server: **Uvicorn** (uvloop engine based) ya **Hypercorn**.

### 2.2 Event Loop, `async def` vs Plain `def`
FastAPI me function signature bohot carefully decide karni chahiye:

| Function Type | Execution Engine | Kaunse Scenarios me Use Karein? |
|---|---|---|
| `async def` | Event Loop Thread directly | Non-blocking I/O (Async Database queries via asyncpg, Async HTTP calls via `httpx.AsyncClient`) |
| `def` (Plain) | External Threadpool (`anyio.to_thread`) | Blocking operations (CPU-bound image processing, legacy sync drivers jaise `psycopg2`, sync disk file reading) |

> **Warning:** Kabhi bhi `async def` function ke andar **synchronous blocking call** (jaise `time.sleep()`, sync `requests.get()`, ya sync DB calls) mat likhein. Yeh pooray ASGI event loop ko freeze kar dega aur sabhi clients ke requests atak jayenge!

### 2.3 Offloading Blocking Sync Code safely in `async def`
Agar kisi async endpoint me third-party sync library execute karni ho:

```python
import time
import anyio
from fastapi import FastAPI

app = FastAPI()

def blocking_legacy_calculation(payload: str) -> str:
    time.sleep(3)  # Heavy blocking operation
    return f"Processed: {payload}"

@app.post("/process-sync-safely")
async def process_sync_safely(data: str):
    # anyio worker thread me execute hoga, event loop block nahi hoga
    result = await anyio.to_thread.run_sync(blocking_legacy_calculation, data)
    return {"status": "success", "result": result}
```

---

## 3. Request Anatomy & Parameter Validations

FastAPI request ko teen primary parts me categorize karta hai:
1. **Path Parameters** (`Path(...)`): URL route ka integral part.
2. **Query Parameters** (`Query(...)`): URL me `?` ke baad aane wali filtering/pagination details.
3. **Request Body** (`Body(...)` ya Pydantic Models): JSON payload.

### 3.1 Path & Query Parameters with Strict Validation

```python
from uuid import UUID
from fastapi import FastAPI, Path, Query, status

app = FastAPI(title="Core Foundation API", version="1.0.0")

@app.get(
    "/organizations/{org_id}/members/{member_id}",
    status_code=status.HTTP_200_OK,
    summary="Fetch Organization Member Details",
    tags=["Organization Members"]
)
async def get_org_member(
    org_id: Annotated[
        UUID, 
        Path(title="Organization UUID", description="Valid RFC 4122 UUID v4")
    ],
    member_id: Annotated[
        int, 
        Path(ge=1, le=1000000, description="Strictly positive sequential identifier")
    ],
    include_inactive: Annotated[
        bool, 
        Query(description="Flag to include deactivated accounts")
    ] = False,
    sort_order: Annotated[
        Literal["asc", "desc"], 
        Query(description="Sorting order for audit history")
    ] = "desc",
    filter_tag: Annotated[
        str | None,
        Query(
            min_length=3,
            max_length=20,
            regex=r"^[a-z]+$",
            description="Lowercase alphabet filter only"
        )
    ] = None,
):
    return {
        "organization": org_id,
        "member_id": member_id,
        "include_inactive": include_inactive,
        "sort_order": sort_order,
        "filter_tag": filter_tag,
    }
```

---

## 4. Custom Error Handling & Exception Lifecycles

Default FastAPI/Pydantic validation 422 error detail provide karta hai, lekin production apps me standard response envelope structure zaroori hota hai.

```python
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

app = FastAPI()

# 1. Custom Global Business Logic Exception
class EntityNotFoundError(Exception):
    def __init__(self, entity_name: str, entity_id: str | int):
        self.entity_name = entity_name
        self.entity_id = entity_id

@app.exception_handler(EntityNotFoundError)
async def entity_not_found_handler(request: Request, exc: EntityNotFoundError):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "success": False,
            "error_code": "RESOURCE_NOT_FOUND",
            "message": f"{exc.entity_name} with identifier '{exc.entity_id}' does not exist.",
            "path": str(request.url)
        }
    )

# 2. Overriding Pydantic Validation Error (HTTP 422)
@app.exception_handler(RequestValidationError)
async def custom_validation_exception_handler(request: Request, exc: RequestValidationError):
    condensed_errors = []
    for error in exc.errors():
        condensed_errors.append({
            "field": " -> ".join([str(loc) for loc in error["loc"]]),
            "issue": error["msg"],
            "type": error["type"]
        })
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error_code": "VALIDATION_FAILED",
            "errors": condensed_errors,
        }
    )
```

---

## 5. Lifespan Events (Application Startup & Shutdown)

FastAPI me purane `@app.on_event("startup")` aur `@app.on_event("shutdown")` ki jagah modern ASGI Lifespan Context Manager use hota hai:

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI

# Mock Resource Clients
class DatabaseConnectionPool:
    async def connect(self): print("🟢 Database connection pool initialized.")
    async def disconnect(self): print("🔴 Database connection pool closed.")

class RedisClient:
    async def init(self): print("🟢 Redis cache connection ready.")
    async def close(self): print("🔴 Redis cache disconnected.")

db_pool = DatabaseConnectionPool()
redis_cache = RedisClient()

@asynccontextmanager
async def app_lifespan(app: FastAPI):
    # Startup actions
    await db_pool.connect()
    await redis_cache.init()
    
    yield  # Application is running and serving requests
    
    # Shutdown actions
    await redis_cache.close()
    await db_pool.disconnect()

app = FastAPI(lifespan=app_lifespan)
```

---

## 6. Production Directory Structure (Phase 1 Ready)

Phase 1 se hi clean architectural isolation follow karni chahiye:

```text
my_project/
│
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app instance, lifespan, exception handlers
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py        # Environment variables & Settings
│   │   └── exceptions.py    # Custom domain exceptions
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── api_router.py # Aggregates all endpoint routers
│   │       └── endpoints/
│   │           ├── __init__.py
│   │           ├── health.py # Health check & telemetry endpoints
│   │           └── items.py  # Path/Query validation endpoints
│   │
│   └── schemas/             # Base validation contracts
│       ├── __init__.py
│       └── common.py
│
├── .env.example
├── pyproject.toml / requirements.txt
└── README.md
```

---

## 7. Phase 1 Checklist & Verification Questions

Khud ki understanding test karne ke liye ye questions verify karein:

1. **Async vs Sync**: Agar ek function me CPU heavy regex calculation ya file compression ho rahi hai, toh use `async def` me likhenge ya `def` me? *(Answer: Plain `def` ya `anyio.to_thread.run_sync` me, taaki event loop block na ho)*.
2. **Annotated Syntax**: `Annotated[int, Query(gt=0)]` ka runtime aur documentation benefit kya hai?
3. **Lifespan**: Startup aur shutdown events ko handle karne ke liye context manager kyu better hai purane event handlers se?