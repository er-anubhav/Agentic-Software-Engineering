"""src.domain.services.job_command_repository_port — CQRS Command Repository Port (Writes)."""
from abc import ABC, abstractmethod
from src.domain.services.relational_store_port import JobRecord


class JobCommandRepositoryPort(ABC):
    """CQRS Command Interface for state mutating write operations."""

    @abstractmethod
    def save_job(self, record: JobRecord) -> None:
        pass

    @abstractmethod
    def delete_job(self, job_id: str) -> None:
        pass
