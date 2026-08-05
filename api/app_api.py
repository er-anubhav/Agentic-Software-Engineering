import uuid
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any, Optional, List
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from orchestrator.workflow import Workflow
from core.config import get_settings

app = FastAPI(
    title="Agentic Software Engineering Platform API",
    version="2.0.0-beta",
    description="Asynchronous Job Queue & Real-time WebSocket Control API for multi-agent autonomous workflows."
)

workflow = Workflow()
settings = get_settings()

# Background Thread Pool Worker Execution
executor = ThreadPoolExecutor(max_workers=4)

# In-Memory Job State Store
JOBS: Dict[str, Dict[str, Any]] = {}

# Active WebSocket Subscriber Connections: job_id -> List[WebSocket]
WEBSOCKET_SUBSCRIBERS: Dict[str, List[WebSocket]] = {}


class ExecuteRequest(BaseModel):
    requirement: str
    repository_path: Optional[str] = None


class JobResponse(BaseModel):
    job_id: str
    status: str
    created_at: float
    websocket_url: str


async def broadcast_job_update(job_id: str, message: Dict[str, Any]):
    subscribers = WEBSOCKET_SUBSCRIBERS.get(job_id, [])
    for ws in list(subscribers):
        try:
            await ws.send_json(message)
        except Exception:
            subscribers.remove(ws)


def run_workflow_job(job_id: str, requirement: str, repository_path: Optional[str]):
    job = JOBS.get(job_id)
    if not job:
        return

    job["status"] = "RUNNING"
    job["started_at"] = time.time()
    job["progress"].append(f"[{time.strftime('%H:%M:%S')}] Workflow execution started.")

    try:
        result = workflow.execute(requirement, repository_path)
        validation_status = result.validation_report.get("status", "UNKNOWN")

        job["status"] = "COMPLETED" if validation_status != "ABORTED" else "ABORTED"
        job["completed_at"] = time.time()
        job["result"] = {
            "functional_requirements": [r.description for r in result.functional_requirements],
            "tasks": result.tasks,
            "validation_status": validation_status,
            "generated_files": list(result.generated_code.keys())
        }
        job["progress"].append(f"[{time.strftime('%H:%M:%S')}] Workflow completed with status: {validation_status}")
    except Exception as ex:
        job["status"] = "FAILED"
        job["completed_at"] = time.time()
        job["error"] = str(ex)
        job["progress"].append(f"[{time.strftime('%H:%M:%S')}] Workflow failed: {ex}")


@app.get("/health")
def health_check():
    return {
        "status": "HEALTHY",
        "app_name": settings.app_name,
        "version": settings.version,
        "active_jobs": len(JOBS)
    }


@app.post("/api/v1/execute", status_code=status.HTTP_202_ACCEPTED)
def submit_workflow_job(req: ExecuteRequest):
    job_id = str(uuid.uuid4())
    created_at = time.time()

    job_data = {
        "job_id": job_id,
        "status": "QUEUED",
        "requirement": req.requirement,
        "repository_path": req.repository_path,
        "created_at": created_at,
        "started_at": None,
        "completed_at": None,
        "progress": [f"[{time.strftime('%H:%M:%S')}] Job queued successfully."],
        "result": None,
        "error": None
    }
    JOBS[job_id] = job_data

    # Dispatch to background thread worker pool without blocking Uvicorn event loop
    executor.submit(run_workflow_job, job_id, req.requirement, req.repository_path)

    return {
        "job_id": job_id,
        "status": "QUEUED",
        "created_at": created_at,
        "websocket_url": f"/api/v1/jobs/{job_id}/ws",
        "status_url": f"/api/v1/jobs/{job_id}"
    }


@app.get("/api/v1/jobs")
def list_jobs():
    return [
        {
            "job_id": j["job_id"],
            "status": j["status"],
            "created_at": j["created_at"],
            "requirement": j["requirement"][:60]
        }
        for j in JOBS.values()
    ]


@app.get("/api/v1/jobs/{job_id}")
def get_job_status(job_id: str):
    job = JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found.")
    return job


@app.websocket("/api/v1/jobs/{job_id}/ws")
async def job_websocket_endpoint(websocket: WebSocket, job_id: str):
    job = JOBS.get(job_id)
    if not job:
        await websocket.close(code=4004, reason="Job not found")
        return

    await websocket.accept()

    if job_id not in WEBSOCKET_SUBSCRIBERS:
        WEBSOCKET_SUBSCRIBERS[job_id] = []
    WEBSOCKET_SUBSCRIBERS[job_id].append(websocket)

    try:
        # Stream initial job state
        await websocket.send_json({
            "event": "INITIAL_STATE",
            "job_id": job_id,
            "status": job["status"],
            "progress": job["progress"]
        })

        # Keep connection open for real-time progress updates
        while True:
            await asyncio.sleep(1)
            current_job = JOBS.get(job_id)
            if current_job:
                await websocket.send_json({
                    "event": "STATUS_UPDATE",
                    "status": current_job["status"],
                    "progress": current_job["progress"],
                    "result": current_job.get("result"),
                    "error": current_job.get("error")
                })
                if current_job["status"] in ("COMPLETED", "FAILED", "ABORTED"):
                    break
    except WebSocketDisconnect:
        pass
    finally:
        if job_id in WEBSOCKET_SUBSCRIBERS and websocket in WEBSOCKET_SUBSCRIBERS[job_id]:
            WEBSOCKET_SUBSCRIBERS[job_id].remove(websocket)
