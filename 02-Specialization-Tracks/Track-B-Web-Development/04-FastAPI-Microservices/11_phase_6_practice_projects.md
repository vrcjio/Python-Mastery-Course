# FastAPI Phase 6 Hands-On Industry Projects

Yeh document 2 real-time aur distributed systems projects provide karta hai jo strictly **Phase 6 (FastAPI BackgroundTasks, Celery Workers, Redis Message Broker, Full-Duplex WebSockets, Room-based Broadcasting, aur Server-Sent Events - SSE)** par based hain.

---

# Project 1: Distributed Bulk Data Importer & Report Engine (Celery + Redis)

### 1. Problem Statement
Ek SaaS analytics platform ko high-volume CSV customer records import karne aur dynamic PDF reports compile karne ke liye ek non-blocking engine develop karna hai:
* Agar user 100,000 rows ka CSV upload kare, toh HTTP request ko 30-40 seconds tak hang nahi hone dena hai.
* System ko turant **`202 Accepted`** response with `task_id` return karna hai.
* Actual parsing aur calculation **Celery Worker** me Redis broker ke through execute ho.
* Frontend client task ka live status (`PENDING`, `PROGRESS`, `SUCCESS`, `FAILURE`) track kar sake with progress percentage.
* External failures ke case me automatic **Exponential Backoff Retries** enabled hon.

### 2. Architecture & File Structure
```
distributed_reporter/
│
├── core/
│   ├── __init__.py
│   └── celery_app.py        # Celery broker configuration
│
├── tasks/
│   ├── __init__.py
│   └── report_tasks.py      # Async background jobs with state updates
│
├── routers/
│   ├── __init__.py
│   └── report_router.py     # HTTP dispatch & task status endpoints
│
└── main.py                  # ASGI entrypoint
```

### 3. Implementation Code

#### 3.1 `core/celery_app.py`
```python
from celery import Celery

REDIS_BROKER_URL = "redis://localhost:6379/1"
REDIS_BACKEND_URL = "redis://localhost:6379/2"

celery_engine = Celery(
    "analytics_pipeline",
    broker=REDIS_BROKER_URL,
    backend=REDIS_BACKEND_URL
)

celery_engine.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,               # Acknowledge task ONLY after completion
    worker_prefetch_multiplier=1        # Fair dispatch across worker cores
)
```

#### 3.2 `tasks/report_tasks.py`
```python
import time
from celery import Task
from celery.utils.log import get_task_logger
from core.celery_app import celery_engine

logger = get_task_logger(__name__)

@celery_engine.task(
    bind=True,
    max_retries=3,
    default_retry_delay=5,
    name="tasks.process_bulk_analytics"
)
def process_bulk_analytics(self: Task, job_id: str, total_batches: int) -> dict:
    """Processes heavy analytics job in batches, updating real-time state progress."""
    try:
        logger.info(f"🚀 [WORKER] Starting Job: {job_id} | Total Batches: {total_batches}")
        
        for current_batch in range(1, total_batches + 1):
            # Heavy calculation simulation per batch
            time.sleep(1)
            
            # Update Task Custom Metadata for Polling Clients
            percent_complete = int((current_batch / total_batches) * 100)
            self.update_state(
                state="PROGRESS",
                meta={
                    "current_batch": current_batch,
                    "total_batches": total_batches,
                    "percent": percent_complete,
                    "status_note": f"Batch {current_batch}/{total_batches} processed."
                }
            )

        logger.info(f"✅ [WORKER] Job '{job_id}' completed successfully.")
        return {
            "job_id": job_id,
            "status": "COMPLETED",
            "download_url": f"https://cdn.enterprise.com/exports/{job_id}.pdf"
        }

    except Exception as exc:
        logger.error(f"❌ [WORKER ERROR] Job failed: {str(exc)}. Retrying...")
        # Exponential backoff formula: 5 * (2 ** retry_count)
        delay = self.default_retry_delay * (2 ** self.request.retries)
        raise self.retry(exc=exc, countdown=delay)
```

#### 3.3 `routers/report_router.py` & `main.py`
```python
# routers/report_router.py
from uuid import uuid4
from fastapi import APIRouter, status
from pydantic import BaseModel, Field
from celery.result import AsyncResult
from core.celery_app import celery_engine
from tasks.report_tasks import process_bulk_analytics

router = APIRouter(prefix="/api/v1/jobs", tags=["Distributed Processing"])

class JobInitiateRequest(BaseModel):
    batch_count: int = Field(default=10, ge=1, le=100, description="Simulated compute chunks")

class JobInitiateResponse(BaseModel):
    job_id: str
    task_id: str
    status: str
    poll_url: str

@router.post("/dispatch", response_model=JobInitiateResponse, status_code=status.HTTP_202_ACCEPTED)
async def dispatch_analytics_job(payload: JobInitiateRequest):
    generated_job_id = f"JOB-{uuid4().hex[:8].upper()}"
    
    # Asynchronous non-blocking dispatch to Redis
    task = process_bulk_analytics.delay(
        job_id=generated_job_id,
        total_batches=payload.batch_count
    )

    return JobInitiateResponse(
        job_id=generated_job_id,
        task_id=task.id,
        status="QUEUED",
        poll_url=f"/api/v1/jobs/status/{task.id}"
    )

@router.get("/status/{task_id}")
async def poll_task_status(task_id: str):
    task = AsyncResult(task_id, app=celery_engine)

    if task.state == "PENDING":
        return {"task_id": task_id, "state": "PENDING", "progress": 0}
    
    elif task.state == "PROGRESS":
        return {
            "task_id": task_id,
            "state": "PROGRESS",
            "meta": task.info  # Contains metadata dictionary emitted from update_state
        }
    
    elif task.state == "SUCCESS":
        return {
            "task_id": task_id,
            "state": "SUCCESS",
            "progress": 100,
            "result": task.result
        }
    
    elif task.state == "FAILURE":
        return {
            "task_id": task_id,
            "state": "FAILURE",
            "error": str(task.info)
        }

    return {"task_id": task_id, "state": task.state}

# main.py
from fastapi import FastAPI

app = FastAPI(title="Distributed Async Processor API", version="1.0.0")
app.include_router(router)
```

---

# Project 2: Real-Time Collaborative Kanban Board & Live Notifications

### 1. Problem Statement
Ek modern agile project management dashboard ke liye real-time coordination service build karni hai:
* Multiple users ek hi Project Board (`workspace_id`) par ek sath kaam kar sakein.
* Jab koi user kisi task card ko `TODO` se `DONE` drag kare, toh pooray board ke connected users ko instant real-time synchronization payload broadcast ho.
* **Full-Duplex WebSockets** connection manager dead-connections ko automatically sweep out kare taaki memory leaks na hon.
* Read-only dashboard screens (jaise TV monitors) ke liye ek lightweight **Server-Sent Events (SSE)** live update stream available ho bina WebSocket connection overhead ke.

### 2. Architecture & Patterns Covered
* **WebSocket Handshake Guard**: Token query parameter check before accepting connection.
* **Scoped Room Broadcasting**: Workspace isolation (`ws_manager.broadcast_to_room`).
* **Protocol Framing**: JSON events (`CARD_MOVED`, `CARD_CREATED`, `USER_TYPING`).
* **Unidirectional SSE Streaming**: `StreamingResponse(media_type="text/event-stream")`.

### 3. Implementation Code

```python
import asyncio
import json
from datetime import datetime, timezone
from typing import Dict, List, Literal, Optional
from uuid import UUID, uuid4
from fastapi import FastAPI, Query, WebSocket, WebSocketDisconnect, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

app = FastAPI(title="Real-Time Collaborative Workspace Engine", version="1.0.0")

# ----------------------------------------------------
# 1. Real-Time Connection Manager
# ----------------------------------------------------
class RealtimeBoardManager:
    def __init__(self):
        # Mapping: {workspace_id: [active_client_websockets]}
        self.workspaces: Dict[str, List[WebSocket]] = {}

    async def connect(self, workspace_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        if workspace_id not in self.workspaces:
            self.workspaces[workspace_id] = []
        self.workspaces[workspace_id].append(websocket)

    def disconnect(self, workspace_id: str, websocket: WebSocket) -> None:
        if workspace_id in self.workspaces:
            if websocket in self.workspaces[workspace_id]:
                self.workspaces[workspace_id].remove(websocket)
            if not self.workspaces[workspace_id]:
                del self.workspaces[workspace_id]

    async def broadcast_to_workspace(
        self,
        workspace_id: str,
        message: dict,
        exclude_client: Optional[WebSocket] = None
    ) -> None:
        if workspace_id not in self.workspaces:
            return

        dead_connections = []
        for client in self.workspaces[workspace_id]:
            if client != exclude_client:
                try:
                    await client.send_json(message)
                except Exception:
                    dead_connections.append(client)

        # Evict terminated connections
        for dead in dead_connections:
            self.disconnect(workspace_id, dead)

board_manager = RealtimeBoardManager()

# In-Memory Board State Mock
WORKSPACE_CARDS: dict[str, list[dict]] = {
    "board_alpha": [
        {"card_id": "c-1", "title": "Setup Async Engine", "status": "DONE"},
        {"card_id": "c-2", "title": "Implement WebSockets", "status": "IN_PROGRESS"},
        {"card_id": "c-3", "title": "Dockerize Celery Nodes", "status": "TODO"},
    ]
}

# ----------------------------------------------------
# 2. WebSocket Full-Duplex Endpoint
# ----------------------------------------------------
@app.websocket("/ws/workspaces/{workspace_id}")
async def workspace_collaboration_socket(
    websocket: WebSocket,
    workspace_id: str,
    user_name: str = Query(..., min_length=2, max_length=50),
    auth_ticket: str = Query(..., description="Single-use connection auth ticket")
):
    # Step 1: Handshake Authentication Gate
    if auth_ticket != "valid-workspace-ticket-2026":
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    # Step 2: Register Client in Specific Board Room
    await board_manager.connect(workspace_id, websocket)

    # Initial Welcome Frame
    await websocket.send_json({
        "event": "SYNC_INITIAL_STATE",
        "workspace_id": workspace_id,
        "cards": WORKSPACE_CARDS.get(workspace_id, [])
    })

    # Broadcast Member Arrival
    await board_manager.broadcast_to_workspace(
        workspace_id,
        {
            "event": "MEMBER_JOINED",
            "user": user_name,
            "timestamp": datetime.now(timezone.utc).isoformat()
        },
        exclude_client=websocket
    )

    try:
        # Step 3: Event Loop for Real-time Inbound Actions
        while True:
            raw_event = await websocket.receive_text()
            event_data = json.loads(raw_event)
            action = event_data.get("action")

            if action == "MOVE_CARD":
                card_id = event_data.get("card_id")
                new_status = event_data.get("new_status")

                # Update in-memory state
                cards = WORKSPACE_CARDS.setdefault(workspace_id, [])
                for card in cards:
                    if card["card_id"] == card_id:
                        card["status"] = new_status

                # Broadcast card movement to peers
                broadcast_payload = {
                    "event": "CARD_MOVED",
                    "card_id": card_id,
                    "new_status": new_status,
                    "moved_by": user_name,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                await board_manager.broadcast_to_workspace(
                    workspace_id,
                    broadcast_payload,
                    exclude_client=None
                )

    except WebSocketDisconnect:
        # Step 4: Graceful Teardown
        board_manager.disconnect(workspace_id, websocket)
        await board_manager.broadcast_to_workspace(
            workspace_id,
            {
                "event": "MEMBER_LEFT",
                "user": user_name,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )

# ----------------------------------------------------
# 3. Server-Sent Events (SSE) Live Feed (Unidirectional)
# ----------------------------------------------------
async def workspace_activity_stream(workspace_id: str):
    """Streams live ping/activity heartbeats to lightweight dashboards."""
    while True:
        payload = {
            "workspace_id": workspace_id,
            "active_collaborators": len(board_manager.workspaces.get(workspace_id, [])),
            "total_cards": len(WORKSPACE_CARDS.get(workspace_id, [])),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        # SSE Wire Protocol: event: <name>\ndata: <json>\n\n
        yield f"event: workspace_tick\n"
        yield f"data: {json.dumps(payload)}\n\n"
        
        await asyncio.sleep(2)

@app.get("/api/v1/workspaces/{workspace_id}/sse-feed")
async def live_dashboard_sse(workspace_id: str):
    return StreamingResponse(
        workspace_activity_stream(workspace_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )
```

---

## 4. How to Run & Verify Phase 6 Projects

### Step 1: Install Dependencies
```bash
pip install fastapi uvicorn[standard] celery redis websockets
```

### Step 2: Running Project 1 (Celery Async Task Engine)
1. **Redis Server start karein**:
   ```bash
   redis-server
   ```
2. **Celery Worker boot karein (Terminal 1)**:
   ```bash
   celery -A core.celery_app.celery_engine worker --loglevel=info --concurrency=2
   ```
3. **FastAPI Server run karein (Terminal 2)**:
   ```bash
   uvicorn main:app --reload --port 8000
   ```
4. **Trigger Task**:
   `POST http://localhost:8000/api/v1/jobs/dispatch` with body `{"batch_count": 8}`.
   Response me `task_id` milega.
5. **Poll Progress**:
   `GET http://localhost:8000/api/v1/jobs/status/{task_id}` har 1-2 second par hit karke terminal aur state me progress increment (`0%` $\rightarrow$ `25%` $\rightarrow$ `75%` $\rightarrow$ `100%`) observe karein.

### Step 3: Running Project 2 (WebSockets & SSE)
1. **Connect via WebSocket client (Postman ya Browser Console)**:
   ```javascript
   const ws = new WebSocket("ws://localhost:8000/ws/workspaces/board_alpha?user_name=DevUser&auth_ticket=valid-workspace-ticket-2026");
   ws.onmessage = (event) => console.log("Received:", JSON.parse(event.data));
   ```
2. **Move a card frame bhej kar test karein**:
   ```javascript
   ws.send(JSON.stringify({
       action: "MOVE_CARD",
       card_id: "c-3",
       new_status: "IN_PROGRESS"
   }));
   ```
3. **SSE Feed test karein**:
   Browser me directly hit karein: `http://localhost:8000/api/v1/workspaces/board_alpha/sse-feed`. Har 2 second par persistent stream updates dikhai denge.