# FastAPI Phase 8 Hands-On Industry Projects

Yeh document 2 production-grade deployment aur DevOps projects provide karta hai jo strictly **Phase 8 (Hardened Multi-Stage Docker, Non-Root Containers, Gunicorn Process Management, Nginx Reverse Proxy & SSL, Docker Compose Multi-Service Orchestration, GitHub Actions CI/CD Pipeline, aur Kubernetes Manifests)** par based hain.

---

# Project 1: Multi-Container Production Microservices Stack (Docker + Compose + Nginx)

### 1. Problem Statement

Ek FastAPI enterprise microservice ko local single-process development environment (`uvicorn --reload`) se nikaal kar ek production-grade, containerized, aur isolated multi-service stack me deploy karna hai:

* Python image ko attack surface aur image size minimize karne ke liye **Multi-Stage Docker build** me convert karein.
* Security compliance ke liye container ko **Non-Root User** (`appuser`) ke under run karein.
* Application process ko **Gunicorn master process** manage kare with **Uvicorn workers** (`uvicorn.workers.UvicornWorker`).
* **Nginx Edge Gateway** configure ho jo external traffic handle kare, client body buffer kare, WebSockets upgrade kare, aur static SSE buffering disable kare (`X-Accel-Buffering: no`).
* Ek unified **`docker-compose.yml`** construct karein jisme **PostgreSQL**, **Redis**, **FastAPI App**, **Celery Worker**, aur **Nginx Gateway** ek private network me orchestrated hon aur healthcheck dependency order follow karein.

---

### 2. Architecture & File Structure

```
production_stack/
│
├── .github/
│   └── workflows/
│       └── deploy.yml          # Project 2 CI/CD workflow
├── app/
│   ├── core/
│   │   ├── config.py           # Pydantic BaseSettings
│   │   └── database.py         # Async SQLAlchemy 2.0 Engine
│   ├── routers/
│   │   └── health.py           # Deep liveness/readiness probes
│   └── main.py                 # ASGI application instance
│
├── docker/
│   ├── Dockerfile              # Multi-stage hardened build
│   ├── gunicorn_conf.py        # Master Gunicorn worker sizing
│   └── nginx.conf              # Reverse proxy & WebSocket config
│
├── k8s/                        # Project 2 Kubernetes manifests
│   ├── deployment.yaml
│   └── service.yaml
│
├── .env.example
├── docker-compose.yml          # Multi-container orchestration
└── requirements.txt
```

---

### 3. Implementation Code

#### 3.1 `docker/gunicorn_conf.py`

```python
import multiprocessing
import os

# Socket binding
bind = os.getenv("BIND", "0.0.0.0:8000")

# CPU Core-based dynamic worker calculation: (2 x Cores) + 1
cores = multiprocessing.cpu_count()
workers = int(os.getenv("WORKERS", (cores * 2) + 1))
worker_class = "uvicorn.workers.UvicornWorker"

# Timeouts & Keepalive
keepalive = 120
timeout = int(os.getenv("TIMEOUT", "120"))
graceful_timeout = int(os.getenv("GRACEFUL_TIMEOUT", "30"))

# Prevent Memory Leaks by recycling workers after N requests
max_requests = 10000
max_requests_jitter = 1000

# Structured stdout/stderr logging
accesslog = "-"
errorlog = "-"
loglevel = os.getenv("LOG_LEVEL", "info")
```

#### 3.2 `docker/Dockerfile`

```dockerfile
# ==========================================
# Stage 1: Build Environment & Wheels Compiler
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
# Stage 2: Hardened Non-Root Production Runner
# ==========================================
FROM python:3.11-slim-bullseye AS runner

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install only minimal runtime libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Security: Create non-root group and user
RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -s /bin/bash -m appuser

# Install wheels from builder stage
COPY --from=builder /build/wheels /wheels
COPY requirements.txt .
RUN pip install --no-cache-dir /wheels/* && rm -rf /wheels

# Copy application source code and configuration
COPY --chown=appuser:appgroup ./app /app/app
COPY --chown=appuser:appgroup ./docker/gunicorn_conf.py /app/gunicorn_conf.py

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=20s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health/liveness || exit 1

CMD ["gunicorn", "-c", "gunicorn_conf.py", "app.main:app"]
```

#### 3.3 `docker/nginx.conf`

```nginx
upstream fastapi_backend {
    server app:8000;
    keepalive 32;
}

server {
    listen 80;
    server_name localhost;

    client_max_body_size 50M;

    # Edge Gateway Headers
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # API Proxy Routing
    location / {
        proxy_pass http://fastapi_backend;
        proxy_http_version 1.1;

        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket Bidirectional Upgrades
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Disable proxy buffering for Real-Time SSE Streams
    location /api/v1/live/ {
        proxy_pass http://fastapi_backend;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_buffering off;
        proxy_cache off;
        proxy_set_header X-Accel-Buffering no;
    }
}
```

#### 3.4 `docker-compose.yml`

```yaml
version: "3.9"

services:
  # Relational Database
  postgres:
    image: postgres:15-alpine
    container_name: enterprise_db
    restart: always
    environment:
      POSTGRES_USER: ${DB_USER:-postgres}
      POSTGRES_PASSWORD: ${DB_PASSWORD:-supersecretpassword}
      POSTGRES_DB: ${DB_NAME:-enterprise_db}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - internal_network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Message Broker & Cache
  redis:
    image: redis:7-alpine
    container_name: enterprise_redis
    restart: always
    command: ["redis-server", "--appendonly", "yes"]
    volumes:
      - redis_data:/data
    networks:
      - internal_network
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  # FastAPI Web Application (Gunicorn + Uvicorn)
  app:
    build:
      context: .
      dockerfile: docker/Dockerfile
    container_name: enterprise_api
    restart: always
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    environment:
      DATABASE_URL: postgresql+asyncpg://${DB_USER:-postgres}:${DB_PASSWORD:-supersecretpassword}@postgres:5432/${DB_NAME:-enterprise_db}
      REDIS_URL: redis://redis:6379/0
      WORKERS: 4
    networks:
      - internal_network
    expose:
      - "8000"

  # Asynchronous Background Worker (Celery Node)
  worker:
    build:
      context: .
      dockerfile: docker/Dockerfile
    container_name: enterprise_worker
    restart: always
    command: ["celery", "-A", "app.core.celery_app.celery_client", "worker", "--loglevel=info", "-c", "2"]
    depends_on:
      redis:
        condition: service_healthy
      postgres:
        condition: service_healthy
    environment:
      DATABASE_URL: postgresql+asyncpg://${DB_USER:-postgres}:${DB_PASSWORD:-supersecretpassword}@postgres:5432/${DB_NAME:-enterprise_db}
      REDIS_URL: redis://redis:6379/0
    networks:
      - internal_network

  # Edge Gateway & Reverse Proxy
  nginx:
    image: nginx:alpine
    container_name: enterprise_gateway
    restart: always
    ports:
      - "80:80"
    volumes:
      - ./docker/nginx.conf:/etc/nginx/conf.d/default.conf:ro
    depends_on:
      - app
    networks:
      - internal_network

networks:
  internal_network:
    driver: bridge

volumes:
  postgres_data:
  redis_data:
```

---

# Project 2: Enterprise CI/CD Pipeline & Kubernetes GitOps Engine

### 1. Problem Statement

Codebase ko automated Continuous Integration / Continuous Deployment (CI/CD) aur cloud orchestration standard par shift karna hai:

* Har GitHub push/PR par **GitHub Actions** trigger ho jo code formatting aur static analysis check kare (`ruff check`, `ruff format`).
* Automated test suite run ho (`pytest-asyncio`) aur code coverage $\ge 85\%$ enforce kare.
* Main branch merge hone par multi-platform Docker container build ho aur securely **GitHub Container Registry (GHCR)** par publish ho.
* **Kubernetes (K8s) Production Manifests** taiyar hon jisme Deployment, ClusterIP Service, Horizontal Pod Autoscaler (HPA), aur **Liveness & Readiness Health Probes** configured hon.

---

### 2. Implementation Code

#### 2.1 `.github/workflows/deploy.yml` (CI/CD Pipeline)

```yaml
name: FastAPI Enterprise CI/CD Pipeline

on:
  push:
    branches: [ "main" ]
  pull_request:
    branches: [ "main" ]

jobs:
  # ==========================================
  # Job 1: Quality Assurance & Automated Tests
  # ==========================================
  audit-and-test:
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
      - name: Checkout Code Repository
        uses: actions/checkout@v4

      - name: Setup Python Runtime 3.11
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: "pip"

      - name: Install Development & Testing Dependencies
        run: |
          python -m pip install --upgrade pip
          pip install ruff pytest pytest-asyncio pytest-cov httpx aiosqlite -r requirements.txt

      - name: Linting & Code Style Verification (Ruff)
        run: |
          ruff check app/
          ruff format --check app/

      - name: Run Pytest Suite with Coverage Enforcement
        env:
          REDIS_URL: redis://localhost:6379/0
          TESTING: "True"
        run: |
          pytest --cov=app --cov-report=term-missing --cov-fail-under=85

  # ==========================================
  # Job 2: Build & Push Hardened Image to GHCR
  # ==========================================
  publish-container:
    needs: audit-and-test
    if: github.ref == 'refs/heads/main' && github.event_name == 'push'
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write

    steps:
      - name: Checkout Repository
        uses: actions/checkout@v4

      - name: Setup Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Authenticate to GitHub Container Registry
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Generate Docker Image Tags & Labels
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ghcr.io/${{ github.repository }}
          tags: |
            type=sha,format=short
            type=raw,value=latest

      - name: Build and Push Production Container
        uses: docker/build-push-action@v5
        with:
          context: .
          file: ./docker/Dockerfile
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

#### 2.2 `k8s/deployment.yaml` (Kubernetes Production Manifest)

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fastapi-enterprise-deployment
  labels:
    app.kubernetes.io/name: fastapi-core
spec:
  replicas: 3
  selector:
    matchLabels:
      app.kubernetes.io/name: fastapi-core
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  template:
    metadata:
      labels:
        app.kubernetes.io/name: fastapi-core
    spec:
      securityContext:
        runAsNonRoot: true
        runAsUser: 10001
        runAsGroup: 10001
        fsGroup: 10001
      containers:
        - name: fastapi-container
          image: ghcr.io/vrcjio/python-mastery-course:latest
          imagePullPolicy: IfNotPresent
          ports:
            - containerPort: 8000
              name: http
          env:
            - name: WORKERS
              value: "3"
            - name: DATABASE_URL
              valueFrom:
                secretKeyRef:
                  name: enterprise-secrets
                  key: database-url
            - name: REDIS_URL
              valueFrom:
                configMapKeyRef:
                  name: enterprise-config
                  key: redis-url
          resources:
            requests:
              memory: "256Mi"
              cpu: "250m"
            limits:
              memory: "512Mi"
              cpu: "1000m"
          # Liveness Probe: Reboots pod if event loop deadlocks
          livenessProbe:
            httpGet:
              path: /health/liveness
              port: 8000
            initialDelaySeconds: 15
            periodSeconds: 10
            timeoutSeconds: 3
            failureThreshold: 3
          # Readiness Probe: Removes pod from load balancer if Postgres/Redis drops
          readinessProbe:
            httpGet:
              path: /health/readiness
              port: 8000
            initialDelaySeconds: 10
            periodSeconds: 5
            timeoutSeconds: 2
            failureThreshold: 2
```

#### 2.3 `k8s/service.yaml` (ClusterIP & Horizontal Pod Autoscaler)

```yaml
apiVersion: v1
kind: Service
metadata:
  name: fastapi-service
  labels:
    app.kubernetes.io/name: fastapi-core
spec:
  type: ClusterIP
  selector:
    app.kubernetes.io/name: fastapi-core
  ports:
    - name: http
      port: 80
      targetPort: 8000
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: fastapi-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: fastapi-enterprise-deployment
  minReplicas: 3
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: 80
```

---

### 4. How to Test & Verify Phase 8 Deployments

#### Step 1: Local Multi-Container Verification (Project 1)

1. Root directory me `docker-compose` build aur run karein:
   ```bash
   docker-compose up --build -d
   ```
2. Check karein ki sabhi containers healthy state me hain:
   ```bash
   docker-compose ps
   ```
   *Expected Output*:
   - `enterprise_db` (healthy)
   - `enterprise_redis` (healthy)
   - `enterprise_api` (Up)
   - `enterprise_worker` (Up)
   - `enterprise_gateway` (Up, ports `0.0.0.0:80->80/tcp`)

3. Edge Nginx gateway ke through health status verify karein:
   ```bash
   curl -i http://localhost/health/readiness
   ```
   *Expected*: `HTTP/1.1 200 OK` with JSON `{"status": "HEALTHY", "checks": {"database": true, "redis": true}}`.

4. Container logs inspect karein:
   ```bash
   docker-compose logs -f app
   ```
   Check karein ki master Gunicorn process ne calculated workers start kiye hain (`[INFO] Booting worker with pid: ...`).

---

#### Step 2: CI/CD Pipeline Verification (Project 2)

1. Changes ko git me add aur push karein:
   ```bash
   git add .
   git commit -m "feat: setup production docker, compose and github actions workflow"
   git push origin main
   ```
2. GitHub Repository me **Actions** tab kholein:
   - Verify karein ki `audit-and-test` job me `ruff` linting aur `pytest` run ho rahe hain.
   - Code coverage threshold ($\ge 85\%$) pass hone ke baad `publish-container` job automatically run hoga.
   - Image successful publish hone par GitHub Packages (`ghcr.io/your-username/repo-name:latest`) me reflect hogi.

---

### 5. Phase 8 Project Checklist

- [ ] Multi-stage Docker build se image size optimize hui?
- [ ] Rootless execution (`USER appuser`) container security standard meet kar raha hai?
- [ ] Gunicorn + Uvicorn worker model active hai (`gunicorn_conf.py`)?
- [ ] Nginx buffer tuning aur WebSocket upgrades correctly proxy ho rahe hain?
- [ ] Docker Compose me container dependencies `service_healthy` condition par based hain?
- [ ] GitHub Actions CI pipeline automated test coverage fail-fast enforce kar raha hai?
- [ ] Kubernetes manifests me liveness aur readiness probes zero-downtime rolling updates ke liye configured hain?