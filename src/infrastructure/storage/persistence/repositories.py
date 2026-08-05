"""
src/storage/persistence/repositories.py — Layer 2: Domain-Specific Repositories.

Explicit repositories wrapping the relational store.
"""
from typing import Dict, Any, Optional
from src.infrastructure.storage.persistence.base_store import RelationalStore, JobRecord


class JobRepository:
    """Explicit repository for platform job management."""

    def __init__(self, store: RelationalStore):
        self.store = store

    def save(self, record: JobRecord) -> None:
        self.store.save_job(record)

    def find_by_id(self, job_id: str) -> Optional[JobRecord]:
        return self.store.get_job(job_id)


class CheckpointRepository:
    """Explicit repository for state checkpoint persistence."""

    def __init__(self, store: RelationalStore):
        self.store = store

    def save(self, checkpoint_id: str, state: Dict[str, Any]) -> None:
        self.store.save_checkpoint(checkpoint_id, state)

    def find_by_id(self, checkpoint_id: str) -> Optional[Dict[str, Any]]:
        return self.store.get_checkpoint(checkpoint_id)
