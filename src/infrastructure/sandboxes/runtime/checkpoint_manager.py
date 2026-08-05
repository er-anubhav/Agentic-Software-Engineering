import json
import os
import time
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
class Checkpoint(BaseModel):
    workflow_id: str
    completed_nodes: List[str] = Field(default_factory=list)
    state_snapshot: Dict[str, Any] = Field(default_factory=dict)
    timestamp: float = Field(default_factory=time.time)
class CheckpointManager:
    """
    Atomic file checkpoint manager for distributed crash recovery and state restoration.
    """
    def __init__(self, storage_dir: str = "runtime_checkpoints"):
        self.storage_dir = storage_dir
        os.makedirs(self.storage_dir, exist_ok=True)
    def save_checkpoint(self, workflow_id: str, completed_nodes: List[str], state_snapshot: Dict[str, Any]) -> str:
        checkpoint = Checkpoint(
            workflow_id=workflow_id,
            completed_nodes=completed_nodes,
            state_snapshot=state_snapshot
        )
        filepath = os.path.join(self.storage_dir, f"{workflow_id}.json")
        temp_filepath = f"{filepath}.tmp"
        with open(temp_filepath, "w", encoding="utf-8") as f:
            json.dump(checkpoint.model_dump(), f, indent=2)
        os.replace(temp_filepath, filepath)
        return filepath
    def load_checkpoint(self, workflow_id: str) -> Optional[Checkpoint]:
        filepath = os.path.join(self.storage_dir, f"{workflow_id}.json")
        if not os.path.exists(filepath):
            return None
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            return Checkpoint(**data)
        except Exception as e:
            return None
    def clear_checkpoint(self, workflow_id: str) -> None:
        filepath = os.path.join(self.storage_dir, f"{workflow_id}.json")
        if os.path.exists(filepath):
            os.remove(filepath)
