"""src.domain.services.checkpoint_repository_port — Segregated Checkpoint Repository Port."""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class CheckpointRepositoryPort(ABC):
    """ISP-compliant repository interface for state checkpoint operations."""

    @abstractmethod
    def save_checkpoint(self, checkpoint_id: str, state: Dict[str, Any]) -> None:
        pass

    @abstractmethod
    def get_checkpoint(self, checkpoint_id: str) -> Optional[Dict[str, Any]]:
        pass
