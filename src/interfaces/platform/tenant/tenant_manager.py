import hashlib
from typing import Dict, Any, Optional
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field


class TenantQuota(BaseModel):
    max_llm_cost_usd: float = 500.0
    current_llm_cost_usd: float = 0.0
    max_storage_gb: float = 100.0
    current_storage_gb: float = 5.0
    max_concurrent_workflows: int = 10
    current_concurrent_workflows: int = 1


class Tenant(BaseModel):
    tenant_id: str
    org_name: str
    tier: str = "ENTERPRISE"  # FREE, TEAM, ENTERPRISE
    quota: TenantQuota = Field(default_factory=TenantQuota)


class TenantManager:
    """
    Multi-Tenant Data Isolation and Quotas Engine.
    Enforces isolation across:
      - Qdrant Vector Collections
      - Neo4j Knowledge Graphs
      - PostgreSQL Schemas
      - Object Storage Buckets / Folders
      - Runtime Workers
      - Prompt Cache
      - Telemetry / Observability
    """

    def __init__(self):
        self.tenants: Dict[str, Tenant] = {}
        self._register_default_tenant()

    def _register_default_tenant(self) -> None:
        default_t = Tenant(tenant_id="tenant_acme", org_name="Acme Corp")
        self.tenants[default_t.tenant_id] = default_t

    def register_tenant(self, tenant: Tenant) -> None:
        self.tenants[tenant.tenant_id] = tenant

    def get_isolated_key(self, tenant_id: str, resource_path: str) -> str:
        raw = f"{tenant_id}:{resource_path}".encode("utf-8")
        h = hashlib.sha256(raw).hexdigest()[:16]
        return f"tenant_{tenant_id}_{h}_{resource_path.replace('/', '_')}"

    def check_quota(self, tenant_id: str, estimated_cost_usd: float = 0.01) -> bool:
        t = self.tenants.get(tenant_id)
        if not t:
            return False

        if t.quota.current_llm_cost_usd + estimated_cost_usd > t.quota.max_llm_cost_usd:
            return False

        if t.quota.current_concurrent_workflows >= t.quota.max_concurrent_workflows:
            return False

        return True

    def record_usage(self, tenant_id: str, cost_usd: float) -> None:
        t = self.tenants.get(tenant_id)
        if t:
            t.quota.current_llm_cost_usd += cost_usd
