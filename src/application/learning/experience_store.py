import time
from typing import Dict, Any, List, Optional
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field


class EngineeringExperience(BaseModel):
    experience_id: str
    workflow_id: str
    task_category: str = "feature_development"
    trajectory: List[str] = Field(default_factory=list)
    repair_history: List[Dict[str, Any]] = Field(default_factory=list)
    human_reviews: List[Dict[str, Any]] = Field(default_factory=list)
    benchmark_outcomes: Dict[str, float] = Field(default_factory=dict)
    tool_chains: List[str] = Field(default_factory=list)
    success: bool = True
    cost_usd: float = 0.05
    duration_sec: float = 12.5
    timestamp: float = Field(default_factory=time.time)


class ExperienceStore:
    """
    Engineering Experience Repository.
    Persists successful and failed workflow trajectories, repair histories,
    human review feedback, benchmark outcomes, and tool execution chains.
    """

    _instance: Optional["ExperienceStore"] = None

    def __init__(self):
        self.experiences: Dict[str, EngineeringExperience] = {}

    @classmethod
    def get_instance(cls) -> "ExperienceStore":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def record_experience(self, exp: EngineeringExperience) -> None:
        self.experiences[exp.experience_id] = exp

    def get_experiences_by_category(self, category: str) -> List[EngineeringExperience]:
        return [e for e in self.experiences.values() if e.task_category.lower() == category.lower()]

    def get_successful_repair_trajectories(self) -> List[EngineeringExperience]:
        return [e for e in self.experiences.values() if e.repair_history and e.success]

    def get_successful_experiences(self) -> List[EngineeringExperience]:
        return [e for e in self.experiences.values() if e.success]
