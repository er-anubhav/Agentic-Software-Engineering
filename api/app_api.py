from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional

from orchestrator.workflow import Workflow
from core.config import get_settings

app = FastAPI(
    title="Agentic Software Engineering Platform API",
    version="2.0.0-alpha",
    description="REST & WebSocket control API for multi-agent autonomous engineering workflow platform."
)

workflow = Workflow()
settings = get_settings()


class ExecuteRequest(BaseModel):
    requirement: str
    repository_path: Optional[str] = None


@app.get("/health")
def health_check():
    return {
        "status": "HEALTHY",
        "app_name": settings.app_name,
        "version": settings.version
    }


@app.post("/api/v1/execute")
def execute_workflow(req: ExecuteRequest):
    try:
        result = workflow.execute(req.requirement, req.repository_path)
        return {
            "status": "COMPLETED",
            "functional_requirements": [r.description for r in result.functional_requirements],
            "tasks": result.tasks,
            "validation_status": result.validation_report.get("status", "UNKNOWN"),
            "generated_files": list(result.generated_code.keys())
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
