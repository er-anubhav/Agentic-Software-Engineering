"""
src.infrastructure.storage.persistence.adapters.sqlite_adapter — Layer 3: Hexagonal SQLite Adapter.
"""
import os
import json
import time
import sqlite3
import logging
import threading
from contextlib import contextmanager
from typing import Dict, Any, Optional, Generator

from src.domain.services.relational_store_port import RelationalStorePort, JobRecord

logger = logging.getLogger(__name__)


class SQLiteAdapter(RelationalStorePort):
    """
    Hexagonal Architecture Adapter for SQLite relational persistence.
    Provides WAL journal mode, connection health-check reconnects, and transaction management.
    """

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or os.getenv("SQLITE_DB_PATH", ":memory:")
        self._local = threading.local()
        self._lock = threading.Lock()
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = getattr(self._local, "connection", None)
        if conn is not None:
            try:
                conn.execute("SELECT 1;")
            except (sqlite3.Error, AttributeError):
                logger.warning("SQLite connection stale or invalid for thread. Re-connecting...")
                conn = None

        if conn is None:
            conn = sqlite3.connect(self.db_path, check_same_thread=False, timeout=15.0)
            conn.row_factory = sqlite3.Row
            if self.db_path != ":memory:":
                conn.execute("PRAGMA journal_mode=WAL;")
            self._local.connection = conn
        return conn

    @contextmanager
    def transaction(self) -> Generator[sqlite3.Connection, None, None]:
        conn = self._get_connection()
        try:
            conn.execute("BEGIN TRANSACTION;")
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error("Transaction rolled back due to error: %s", e, exc_info=True)
            raise

    def _init_db(self) -> None:
        try:
            with self._lock:
                conn = self._get_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS jobs (
                        job_id TEXT PRIMARY KEY,
                        tenant_id TEXT,
                        status TEXT,
                        payload TEXT,
                        created_at REAL
                    )
                """)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS checkpoints (
                        checkpoint_id TEXT PRIMARY KEY,
                        state TEXT,
                        saved_at REAL
                    )
                """)
                conn.commit()
        except Exception as e:
            logger.error("Failed to initialize SQLite database schema: %s", e, exc_info=True)
            raise

    def save_job(self, record: JobRecord) -> None:
        try:
            conn = self._get_connection()
            with conn:
                conn.execute(
                    "INSERT OR REPLACE INTO jobs (job_id, tenant_id, status, payload, created_at) VALUES (?, ?, ?, ?, ?)",
                    (record.job_id, record.tenant_id, record.status, json.dumps(record.payload), record.created_at)
                )
        except Exception as e:
            logger.error("SQLite error saving job '%s': %s", record.job_id, e, exc_info=True)
            raise

    def get_job(self, job_id: str) -> Optional[JobRecord]:
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT job_id, tenant_id, status, payload, created_at FROM jobs WHERE job_id = ?", (job_id,))
            row = cursor.fetchone()
            if row:
                return JobRecord(
                    job_id=row["job_id"],
                    tenant_id=row["tenant_id"],
                    status=row["status"],
                    payload=json.loads(row["payload"]) if row["payload"] else {},
                    created_at=row["created_at"]
                )
            return None
        except Exception as e:
            logger.error("SQLite error fetching job '%s': %s", job_id, e, exc_info=True)
            return None

    def save_checkpoint(self, checkpoint_id: str, state: Dict[str, Any]) -> None:
        try:
            conn = self._get_connection()
            with conn:
                conn.execute(
                    "INSERT OR REPLACE INTO checkpoints (checkpoint_id, state, saved_at) VALUES (?, ?, ?)",
                    (checkpoint_id, json.dumps(state), time.time())
                )
        except Exception as e:
            logger.error("SQLite error saving checkpoint '%s': %s", checkpoint_id, e, exc_info=True)
            raise

    def get_checkpoint(self, checkpoint_id: str) -> Optional[Dict[str, Any]]:
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT state FROM checkpoints WHERE checkpoint_id = ?", (checkpoint_id,))
            row = cursor.fetchone()
            if row:
                return json.loads(row["state"])
            return None
        except Exception as e:
            logger.error("SQLite error fetching checkpoint '%s': %s", checkpoint_id, e, exc_info=True)
            return None
