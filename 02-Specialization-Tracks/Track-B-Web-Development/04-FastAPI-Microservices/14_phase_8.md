# FastAPI Phase 8 Developer Handbook: Deployment, Scaling & DevOps

Yeh handbook FastAPI applications ko enterprise cloud environments me package karne (**Multi-Stage Docker**, **Non-Root Containers**), manage karne (**Gunicorn + Uvicorn Workers**), secure karne (**Nginx Reverse Proxy & SSL**), orchestrate karne (**Docker Compose**, **Kubernetes Health Probes**), aur continuously deliver karne (**GitHub Actions CI/CD**) ka exhaustive reference guide hai.

---

## 1. Production Process Architecture: Gunicorn + Uvicorn Workers

Local development me hum `uvicorn app.main:app --reload` use karte hain, jo single-process dev server hai. Production me high concurrency aur process recovery ke liye **Gunicorn (Master Process Manager)** ke under **Uvicorn (Async ASGI Workers)** chalana mandatory hota hai.

```
Incoming Traffic (Port 80/443)
              │
              ▼
    [ Nginx Reverse Proxy ]
              │
              ▼ (Reverse Proxy Unix Socket / Port 8000)
    [ Gunicorn Master Process ]
         ├── Worker 1: Uvicorn (uvloop + httptools)
         ├── Worker 2: Uvicorn (uvloop + httptools)
         ├── Worker 3: Uvicorn (uvloop + httptools)
         └── Worker 4: Uvicorn (uvloop + httptools)
```

### 1.1 Worker Allocation Formula
Master process ko system ke available CPU cores ke hisab se scale kiya jata hai:
$$\text{Workers} = (2 \times \text{CPU Cores}) + 1$$

*Example*: 2 Core VPS/EC2 instance ke liye: $(2 \times 2) + 1 = 5 \text{ workers}$.

### 1.2 Production Gunicorn Configuration (`gunicorn_conf.py`)

```python
import multiprocessing
import os

# Server socket binding
bind = os.getenv("BIND", "0.0.0.0:8000")

# Worker execution mechanics
workers = int(os.getenv("WORKERS", (multiprocessing.cpu_count() * 2) + 1))
worker_class = "uvicorn.workers.UvicornWorker"

# Timeout & Keep-Alive settings
keepalive = 120
timeout = int(os.getenv("TIMEOUT", "120"))
graceful_timeout = int(os.getenv("GRACEFUL_TIMEOUT", "30"))

# Worker memory leak prevention (auto restart workers after processing N requests)
max_requests = 10000
max_requests_jitter = 1000

# Logging formatting
loglevel = os.getenv("LOG_LEVEL", "info")
accesslog = "-"  # Stdout
errorlog = "-"   # Stderr
```

---

## 2. Hardened Multi-Stage Dockerfile

Production containers minimal, secure, aur rootless hone chahiye taaki container breakout attacks na ho sakein.

### 2.1 Multi-Stage `Dockerfile`

```dockerfile
# ==========================================
# Stage 1: Build Environment & Wheels
# ==========================================
FROM python:3.11-slim-bullseye AS builder

WORKDIR /build

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Compile python dependencies into isolated wheels
RUN pip install --no-cache-dir --upgrade pip && \
    pip wheel --no-cache-dir --no-deps --wheel-dir /build/wheels -r requirements.txt


# ==========================================
# Stage 2: Minimal Distroless / Hardened Runner
# ==========================================
FROM python:3.11-slim-bullseye AS runner

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"

# Runtime libraries only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Non-root user creation (Security Best Practice)
RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -s /bin/bash -m appuser

# Copy wheels from builder and install
COPY --from=builder /build/wheels /wheels
COPY requirements.txt .
RUN pip install --no-cache-dir /wheels/* && rm -rf /wheels

# Copy application source code
COPY --chown=appuser:appgroup . /app

# Switch to non-root user
USER appuser

EXPOSE 8000

# Healthcheck for container engines
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Launch Gunicorn with Uvicorn workers
CMD ["gunicorn", "-c", "gunicorn_conf.py", "app.main:app"]
```

---

## 3. Reverse Proxy Configuration (Nginx)

Nginx incoming client requests ko terminate karta hai, SSL certificates handle karta hai, slow clients ko buffer karta hai, aur WebSockets connections upgrade karta hai.

### 3.1 `nginx.conf`

```nginx
upstream fastapi_cluster {
    server app:8000;
    keepalive 32;
}

server {
    listen 80;
    server_name api.enterprise.com;
    
    # Redirect all HTTP traffic to HTTPS
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.enterprise.com;

    # SSL Certificates
    ssl_certificate /etc/letsencrypt/live/api.enterprise.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.enterprise.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Security Headers
    add_header X-Content-Type-Options nosniff always;
    add_header X-Frame-Options DENY always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Client payload size (Match FastAPI file upload limit)
    client_max_body_size 50M;

    # Proxy to FastAPI Cluster
    location / {
        proxy_pass http://fastapi_cluster;
        proxy_http_version 1.1;

        # Header forwarding
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Disable proxy buffering for SSE endpoints
    location /api/v1/live/ {
        proxy_pass http://fastapi_cluster;
        proxy_set_header Host $host;
        proxy_buffering off;
        proxy_cache off;
        proxy_set_header X-Accel-Buffering no;
    }
}
```

---

## 4. Complete Orchestration: `docker-compose.yml`

Yeh compose specification **FastAPI Backend**, **PostgreSQL**, **Redis Broker**, **Celery Worker Node**, aur **Nginx Gateway** ko private network me orchestrate karti hai.

```yaml
version: "3.9"

services:
  # Database Service
  postgres:
    image: postgres:15-alpine
    container_name: enterprise_db
    restart: always
    environment:
      POSTGRES_USER: ${DB_USER:-postgres}
      POSTGRES_PASSWORD: ${DB_PASSWORD:-securepassword}
      POSTGRES_DB: ${DB_NAME:-enterprise_db}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - backend_network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  # In-Memory Cache & Message Broker
  redis:
    image: redis:7-alpine
    container_name: enterprise_redis
    restart: always
    command: ["redis-server", "--appendonly", "yes"]
    volumes:
      - redis_data:/data
    networks:
      - backend_network
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Primary Web Application (Gunicorn + Uvicorn)
  app:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: enterprise_api
    restart: always
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    env_file:
      - .env
    networks:
      - backend_network
    expose:
      - "8000"

  # Distributed Background Worker (Celery)
  worker:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: enterprise_worker
    restart: always
    command: ["celery", "-A", "app.core.celery_app.celery_client", "worker", "--loglevel=info", "-c", "4"]
    depends_on:
      - redis
      - postgres
    env_file:
      - .env
    networks:
      - backend_network

  # Edge Gateway & Reverse Proxy
  nginx:
    image: nginx:alpine
    container_name: enterprise_gateway
    restart: always
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/conf.d/default.conf:ro
    depends_on:
      - app
    networks:
      - backend_network

networks:
  backend_network:
    driver: bridge

volumes:
  postgres_data:
  redis_data:
```

---

## 5. Production CI/CD Pipeline (GitHub Actions)

Har git commit aur pull request par tests run karne, linting verify karne, aur successful merge par production container publish karne ka workflow:

```yaml
# .github/workflows/deploy.yml
name: FastAPI Enterprise CI/CD Pipeline

on:
  push:
    branches: [ "main" ]
  pull_request:
    branches: [ "main" ]

jobs:
  lint-and-test:
    runs-on: ubuntu-latest
    services:
      redis:
        image: redis:7-alpine
        ports:
          - 6379:6379
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - name: Checkout Code
        uses: actions/checkout@v4

      - name: Set up Python 3.11
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: "pip"

      - name: Install Linting & Test Dependencies
        run: |
          python -m pip install --upgrade pip
          pip install ruff pytest pytest-asyncio pytest-cov httpx -r requirements.txt

      - name: Code Quality & Linting Check (Ruff)
        run: |
          ruff check .
          ruff format --check .

      - name: Run Test Suite with Coverage
        env:
          REDIS_URL: redis://localhost:6379/0
          TESTING: "True"
        run: |
          pytest --cov=app --cov-report=xml --cov-fail-under=85

  build-and-publish:
    needs: lint-and-test
    if: github.ref == 'refs/heads/main' && github.event_name == 'push'
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Code
        uses: actions/checkout@v4

      - name: Log in to GitHub Container Registry (GHCR)
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Extract Docker Metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ghcr.io/${{ github.repository }}
          tags: |
            type=sha,format=long
            type=raw,value=latest

      - name: Build & Push Production Image
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
```

---

## 6. Kubernetes Readiness & Liveness Probes

Kubernetes orchestration me FastAPI pods ke status check karne ke liye do critical health endpoints require hote hain:

```python
# app/routers/health.py
from fastapi import APIRouter, status, Response
from sqlalchemy import text
from app.core.database import AsyncSessionLocal
import redis.asyncio as aioredis

router = APIRouter(tags=["Health Telemetry"])

@router.get("/health/liveness", status_code=status.HTTP_200_OK)
async def liveness_probe():
    """Confirms ASGI process is alive and not frozen by event loop deadlocks."""
    return {"status": "ALIVE"}

@router.get("/health/readiness", status_code=status.HTTP_200_OK)
async def readiness_probe(response: Response):
    """Deep check verifying upstream dependencies (Postgres + Redis) are operational."""
    checks = {"database": False, "redis": False}

    # 1. Check Database
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
            checks["database"] = True
    except Exception:
        checks["database"] = False

    # 2. Check Redis
    try:
        r = aioredis.from_url("redis://localhost:6379/0")
        await r.ping()
        await r.close()
        checks["redis"] = True
    except Exception:
        checks["redis"] = False

    if not all(checks.values()):
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "DEGRADED", "checks": checks}

    return {"status": "HEALTHY", "checks": checks}
```

---

## 7. Phase 8 Mastery Checklist

- [ ] Kya local dev server (`--reload`) ki jagah production me **Gunicorn + UvicornWorker** process model use ho raha hai?
- [ ] Kya `Dockerfile` multi-stage build follow karta hai aur container **non-root user (`appuser`)** se run hota hai?
- [ ] Kya Nginx reverse proxy me WebSockets (`Upgrade: connection`) aur SSE (`X-Accel-Buffering: no`) correctly configured hain?
- [ ] Kya `docker-compose.yml` me sabhi dependent containers ke liye `healthcheck` configured hai?
- [ ] Kya Kubernetes/Docker deployments ke liye `/health/liveness` aur `/health/readiness` deep checks implemented hain?
- [ ] Kya GitHub Actions CI pipeline automated linting (`ruff`), unit tests, coverage verification, aur container registry builds run karta hai?