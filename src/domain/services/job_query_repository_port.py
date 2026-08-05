"""src.domain.services.job_query_repository_port — CQRS Query Repository Port (Reads)."""
from abc import ABC, abstractmethod
from typing import Optional, List
from src.domain.services.relational_store_port import JobRecord


class JobQueryRepositoryPort(ABC):
    """CQRS Query Interface for side-effect-free read operations."""

    @abstractmethod
    def get_job(self, job_id: str) -> Optional[JobRecord]:
        pass

    @abstractmethod
    def list_jobs(self, tenant_id: str, limit: int = 50) -> List[JobRecord]:
        pass
