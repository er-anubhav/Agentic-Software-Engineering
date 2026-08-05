"""src.domain.services.job_repository_port — Segregated Job Repository Port."""
from abc import ABC, abstractmethod
from typing import Optional
from src.domain.services.relational_store_port import JobRecord


class JobRepositoryPort(ABC):
    """ISP-compliant repository interface for job operations."""

    @abstractmethod
    def save_job(self, record: JobRecord) -> None:
        pass

    @abstractmethod
    def get_job(self, job_id: str) -> Optional[JobRecord]:
        pass
