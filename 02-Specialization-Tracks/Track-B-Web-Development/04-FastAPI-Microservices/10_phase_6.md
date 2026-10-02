# FastAPI Phase 6 Developer Handbook: Background Tasks, Distributed Queues & Real-Time Communication

Yeh handbook FastAPI me non-blocking asynchronous architectures, distributed background workers (**Celery + Redis**), full-duplex persistent connections (**WebSockets**), aur unidirectional event streaming (**Server-Sent Events - SSE**) ka enterprise reference guide hai.

---

## 1. Async Task Paradigms: Native vs Distributed

Jab koi request compute-heavy ya network-heavy ho (jaise PDF report banana, image resize karna, email dispatch karna), client ko synchronous wait karana latency choke create karta hai.

### 1.1 Architecture Decision Matrix

| Metric | FastAPI `BackgroundTasks` | Distributed Queue (Celery / ARQ) |
| :--- | :--- | :--- |
| **Execution Environment** | Same ASGI application process | Independent external worker processes |
| **Persistence** | In-Memory (Server crash par task loss) | Redis / RabbitMQ broker backed (Fault-tolerant) |
| **Best For** | Audit logs, fire-and-forget emails, temp file cleanup | CSV imports, video transcoding, bulk notifications |
| **Scalability** | App server ke resources par dependent | Auto-scaled workers independent of web traffic |

---

## 2. Native `BackgroundTasks` Engine

FastAPI ka built-in `BackgroundTasks` Starlette par based hai. Yeh response client ko return hone ke **baad** execute hota hai.

```python
# app/routers/tasks_native.py
import asyncio
from datetime import datetime, timezone
from pathlib import Path
from fastapi import APIRouter, BackgroundTasks, status
from pydantic import BaseModel, EmailStr

router = APIRouter(prefix="/api/v1/notifications", tags=["Notifications"])

class EmailNotificationPayload(BaseModel):
    recipient_email: EmailStr
    subject: str
    message: str

def write_audit_log_to_disk(recipient: str, subject: str) -> None:
    """Synchronous file I/O executed inside threadpool by background worker."""
    log_file = Path("audit_logs.txt")
    with log_file.open("a", encoding="utf-8") as f:
        timestamp = datetime.now(timezone.utc).isoformat()
        f.write(f"[{timestamp}] EMAIL_DISPATCHED to {recipient} | Subject: {subject}\n")

async def send_simulated_email(recipient: str, subject: str, body: str) -> None:
    """Simulated async email sender."""
    await asyncio.sleep(2)  # Non-blocking network delay simulation
    print(f"📧 [DISPATCH COMPLETE] Sent to {recipient} | Subject: '{subject}'")

@router.post("/send-alert", status_code=status.HTTP_202_ACCEPTED)
async def dispatch_notification(
    payload: EmailNotificationPayload,
    bg_tasks: BackgroundTasks
):
    # Enqueue tasks to run AFTER returning the 202 Accepted response
    bg_tasks.add_task(send_simulated_email, payload.recipient_email, payload.subject, payload.message)
    bg_tasks.add_task(write_audit_log_to_disk, payload.recipient_email, payload.subject)

    return {
        "status": "QUEUED",
        "message": "Notification scheduled for asynchronous dispatch.",
        "recipient": payload.recipient_email
    }
```

---

## 3. Distributed Processing with Celery & Redis

Production enterprise architectures me heavy tasks ko dedicated compute worker nodes par push kiya jata hai.

```
Client ──▶ FastAPI (API Gateway)
                 │
                 ├── (1) celery_app.send_task()
                 ▼
          [Redis Message Broker]
                 │
                 ├── (2) Worker picks up task from queue
                 ▼
          [Celery Worker Nodes] ──▶ [Redis / DB Result Backend]
```

### 3.1 Celery Instance Initialization

```python
# app/core/celery_app.py
from celery import Celery

# Redis as both Broker and Result Backend
REDIS_BROKER_URL = "redis://localhost:6379/1"
REDIS_BACKEND_URL = "redis://localhost:6379/2"

celery_client = Celery(
    "worker_pool",
    broker=REDIS_BROKER_URL,
    backend=REDIS_BACKEND_URL,
)

celery_client.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,        # Hard kill after 5 minutes
    task_soft_time_limit=240,   # Graceful exception after 4 minutes
)
```

### 3.2 Celery Task with Exponential Backoff Retries

```python
# app/tasks/report_tasks.py
import time
from celery.utils.log import get_task_logger
from app.core.celery_app import celery_client

logger = get_task_logger(__name__)

@celery_client.task(
    bind=True,
    max_retries=3,
    default_retry_delay=5,  # 5s, 10s, 20s exponential progression
    name="tasks.generate_pdf_report"
)
def generate_pdf_report(self, report_id: str, row_count: int) -> dict:
    try:
        logger.info(f"🚀 Processing report '{report_id}' with {row_count} records...")
        
        # Heavy computation simulation
        time.sleep(4) 
        
        # Simulating random network failure to demonstrate retries
        # if random.random() < 0.3: raise ConnectionError("Temporary upstream timeout")

        logger.info(f"✅ Report '{report_id}' generated successfully.")
        return {
            "report_id": report_id,
            "status": "COMPLETED",
            "file_url": f"https://cdn.enterprise.com/reports/{report_id}.pdf"
        }
    except Exception as exc:
        logger.warning(f"⚠️ Task failed. Retrying... Error: {str(exc)}")
        # Exponential backoff: 5 * (2 ** retry_number)
        countdown = self.default_retry_delay * (2 ** self.request.retries)
        raise self.retry(exc=exc, countdown=countdown)
```

### 3.3 Triggering & Polling Tasks from FastAPI

```python
# app/routers/reports.py
from fastapi import APIRouter, HTTPException, status
from celery.result import AsyncResult
from app.core.celery_app import celery_client
from app.tasks.report_tasks import generate_pdf_report

router = APIRouter(prefix="/api/v1/reports", tags=["Distributed Reports"])

@router.post("/generate", status_code=status.HTTP_202_ACCEPTED)
async def request_report_generation(report_id: str, row_count: int = 5000):
    # Non-blocking async dispatch to Redis broker
    task = generate_pdf_report.delay(report_id=report_id, row_count=row_count)
    return {
        "task_id": task.id,
        "status": "PENDING",
        "check_status_url": f"/api/v1/reports/status/{task.id}"
    }

@router.get("/status/{task_id}")
async def check_task_status(task_id: str):
    task_result = AsyncResult(task_id, app=celery_client)
    
    response = {
        "task_id": task_id,
        "state": task_result.state,
    }

    if task_result.state == "SUCCESS":
        response["result"] = task_result.result
    elif task_result.state == "FAILURE":
        response["error"] = str(task_result.info)

    return response
```

---

## 4. Full-Duplex Real-Time Communication: WebSockets

WebSockets single TCP connection par bidirectional, persistent, low-overhead communication allow karta hai. Chat systems, live tracking, aur collaborative dashboards is pattern par kaam karte hain.

### 4.1 Production WebSocket Connection Manager

Multiple clients, rooms/channels, aur dead-connection cleanup handle karne ke liye Manager pattern mandatory hai:

```python
# app/core/websocket_manager.py
from typing import Dict, List
from fastapi import WebSocket

class WebSocketConnectionManager:
    def __init__(self):
        # Room-based connection mapping: {room_id: [active_websocket_connections]}
        self.active_rooms: Dict[str, List[WebSocket]] = {}

    async def connect(self, room_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        if room_id not in self.active_rooms:
            self.active_rooms[room_id] = []
        self.active_rooms[room_id].append(websocket)

    def disconnect(self, room_id: str, websocket: WebSocket) -> None:
        if room_id in self.active_rooms:
            if websocket in self.active_rooms[room_id]:
                self.active_rooms[room_id].remove(websocket)
            if not self.active_rooms[room_id]:
                del self.active_rooms[room_id]

    async def send_personal_message(self, message: dict, websocket: WebSocket) -> None:
        await websocket.send_json(message)

    async def broadcast_to_room(self, room_id: str, message: dict, exclude_sender: WebSocket | None = None) -> None:
        """Broadcasts payload to all clients connected to a specific channel/room."""
        if room_id not in self.active_rooms:
            return

        dead_connections = []
        for connection in self.active_rooms[room_id]:
            if connection != exclude_sender:
                try:
                    await connection.send_json(message)
                except Exception:
                    dead_connections.append(connection)

        # Cleanup connections that dropped abruptly
        for dead_conn in dead_connections:
            self.disconnect(room_id, dead_conn)

ws_manager = WebSocketConnectionManager()
```

### 4.2 WebSocket Route with Auth & Message Dispatch

```python
# app/routers/chat_ws.py
from datetime import datetime, timezone
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, status

from app.core.websocket_manager import ws_manager

router = APIRouter(prefix="/ws", tags=["WebSockets"])

@router.websocket("/rooms/{room_id}")
async def room_websocket_endpoint(
    websocket: WebSocket,
    room_id: str,
    client_name: str = Query(..., min_length=2, max_length=30),
    auth_token: str | None = Query(None)
):
    # Step 1: Handshake Authentication Guard
    if auth_token != "super-secure-ws-key-101":
        # 1008 = Policy Violation in WebSocket close codes
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    # Step 2: Accept Connection & Register in Room
    await ws_manager.connect(room_id, websocket)
    
    # Broadcast Join Notification
    await ws_manager.broadcast_to_room(
        room_id,
        {
            "event": "USER_JOINED",
            "sender": "SYSTEM",
            "message": f"'{client_name}' entered the room.",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    )

    try:
        # Step 3: Listen for Inbound Frames
        while True:
            data = await websocket.receive_text()
            
            # Broadcast message to room peers
            payload = {
                "event": "CHAT_MESSAGE",
                "sender": client_name,
                "text": data,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            await ws_manager.broadcast_to_room(room_id, payload, exclude_sender=None)

    except WebSocketDisconnect:
        # Step 4: Graceful Teardown on Disconnect
        ws_manager.disconnect(room_id, websocket)
        await ws_manager.broadcast_to_room(
            room_id,
            {
                "event": "USER_LEFT",
                "sender": "SYSTEM",
                "message": f"'{client_name}' disconnected.",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
```

---

## 5. Server-Sent Events (SSE)

Agar server ko sirf **unidirectional** updates bhejne hain (e.g., live stock price ticks, cryptocurrency updates, LLM token streaming, task progress bars), toh WebSockets ka overhead lene ke bajaye **Server-Sent Events (SSE)** best suited standard protocol hai.

SSE standard HTTP connection par `text/event-stream` format use karta hai.

```python
# app/routers/sse_stream.py
import asyncio
import json
import random
from typing import AsyncGenerator
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

router = APIRouter(prefix="/api/v1/live", tags=["SSE Streaming"])

async def mock_stock_ticker_stream(symbol: str) -> AsyncGenerator[str, None]:
    """Generates SSE compatible frames: data: <payload>\n\n"""
    current_price = 150.00
    
    while True:
        # Simulate price volatility
        delta = round(random.uniform(-1.50, 1.50), 2)
        current_price = round(current_price + delta, 2)
        
        event_payload = {
            "symbol": symbol,
            "price": current_price,
            "change": delta
        }

        # SSE Protocol standard wire specification
        yield f"event: price_update\n"
        yield f"data: {json.dumps(event_payload)}\n\n"

        await asyncio.sleep(1)  # Tick every second

@router.get("/ticker/{symbol}")
async def stream_live_prices(symbol: str):
    return StreamingResponse(
        mock_stock_ticker_stream(symbol.upper()),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Critical for Nginx reverse proxy buffering bypass
        }
    )
```

---

## 6. Execution & Worker Boot Commands

### Step 1: Install Dependencies
```bash
pip install fastapi uvicorn[standard] celery redis websockets
```

### Step 2: Start Redis Broker
```bash
redis-server
```

### Step 3: Start Celery Worker Node (Terminal 1)
```bash
celery -A app.core.celery_app.celery_client worker --loglevel=info --concurrency=4
```

### Step 4: Run FastAPI Application (Terminal 2)
```bash
uvicorn app.main:app --reload --port 8000
```

---

## 7. Phase 6 Mastery Checklist

- [ ] Lightweight tasks ke liye `BackgroundTasks` aur heavy CPU/I/O tasks ke liye `Celery` me clear distinction pata hai?
- [ ] Celery tasks me `bind=True`, `max_retries`, aur exponential backoff retry mechanics configured hain?
- [ ] WebSocket connection manager me dead connection memory-leak protection shamil hai?
- [ ] WebSockets me query param ya header level handshake authentication verified hai?
- [ ] Unidirectional streaming ke liye `text/event-stream` SSE specification (`event: ...\ndata: ...\n\n`) correctly implemented hai?
- [ ] Reverse proxies (jaise Nginx) ke piche SSE chalate waqt `X-Accel-Buffering: no` header ka purpose clear hai?