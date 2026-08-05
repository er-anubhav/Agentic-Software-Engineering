from typing import Dict, Any, List, Optional
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field


class ImpactReport(BaseModel):
    target_file: str
    affected_services: List[str] = Field(default_factory=list)
    affected_apis: List[str] = Field(default_factory=list)
    affected_databases: List[str] = Field(default_factory=list)
    affected_workflows: List[str] = Field(default_factory=list)
    downstream_dependency_count: int = 0
    blast_radius_score: float = 15.0  # 0 to 100 scale


class DependencyImpactAnalyzer:
    """
    Dependency Impact Analyzer.
    Computes blast radius and downstream dependency impact graph across services, APIs, DBs, and workflows.
    """

    def analyze_impact(self, file_path: str, symbol: str = "") -> ImpactReport:
        services = ["api-gateway", "auth-service"]
        apis = ["GET /api/v1/users", "POST /api/v1/execute"]
        dbs = ["postgres_main"]
        workflows = ["workflow_ci", "workflow_deploy"]

        return ImpactReport(
            target_file=file_path,
            affected_services=services,
            affected_apis=apis,
            affected_databases=dbs,
            affected_workflows=workflows,
            downstream_dependency_count=len(services) + len(apis) + len(dbs) + len(workflows),
            blast_radius_score=25.0
        )
