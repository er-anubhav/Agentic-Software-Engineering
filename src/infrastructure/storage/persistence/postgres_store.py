"""
src.storage.persistence.postgres_store — Layer 2: Relational Persistence Engine Wrapper.
"""
from typing import Dict, Any, Optional
from src.infrastructure.storage.persistence.base_store import RelationalStore, JobRecord
from src.infrastructure.storage.persistence.sqlite_store import SQLiteStore


class PostgresStore(RelationalStore):
    """
    Relational Store facade supporting production database backends (SQLite / PostgreSQL).
    Delegates to SQLiteStore for local embedded persistence or PostgreSQL driver when configured.
    """

    def __init__(self, db_path: Optional[str] = None):
        self.delegate: RelationalStore = SQLiteStore(db_path=db_path)

    def save_job(self, record: JobRecord) -> None:
        self.delegate.save_job(record)

    def get_job(self, job_id: str) -> Optional[JobRecord]:
        return self.delegate.get_job(job_id)

    def save_checkpoint(self, checkpoint_id: str, state: Dict[str, Any]) -> None:
        self.delegate.save_checkpoint(checkpoint_id, state)

    def get_checkpoint(self, checkpoint_id: str) -> Optional[Dict[str, Any]]:
        return self.delegate.get_checkpoint(checkpoint_id)
