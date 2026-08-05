"""
src.domain.entities.state — Layer 2: Domain State Entities.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import uuid
import time


@dataclass
class Requirement:
    id: str
    description: str


@dataclass
class RequirementResult:
    functional_requirements: List[Requirement] = field(default_factory=list)
    non_functional_requirements: List[Requirement] = field(default_factory=list)
    assumptions: List[Requirement] = field(default_factory=list)
    ambiguities: List[Requirement] = field(default_factory=list)
    risks: List[Requirement] = field(default_factory=list)


@dataclass
class PlanResult:
    tasks: List[str] = field(default_factory=list)
    planner_nodes: List[Any] = field(default_factory=list)


@dataclass
class AnalysisResult:
    repository_path: str = ""
    codebase_analysis: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ArchitectureResult:
    architecture: str = ""
    components: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class DesignResult:
    design: Dict[str, Any] = field(default_factory=dict)
    api_spec: Dict[str, Any] = field(default_factory=dict)
    database_schema: Dict[str, str] = field(default_factory=dict)


@dataclass
class ValidationResult:
    status: str = "PASS"
    checks: List[Dict[str, Any]] = field(default_factory=list)
    summary: str = ""


@dataclass
class EngineeringState:
    """
    Engineering State Entity tracking workflow lifecycle.
    """
    workflow_id: str = field(default_factory=lambda: f"wf_{uuid.uuid4().hex[:8]}")
    user_prompt: str = ""
    repository_path: str = ""
    current_phase: str = "INIT"
    execution_status: str = "PENDING"
    requirements: RequirementResult = field(default_factory=RequirementResult)
    tasks: List[str] = field(default_factory=list)
    planner_nodes: List[Any] = field(default_factory=list)
    execution_plan: Dict[str, Any] = field(default_factory=dict)
    analysis: AnalysisResult = field(default_factory=AnalysisResult)
    architecture: ArchitectureResult = field(default_factory=ArchitectureResult)
    design: DesignResult = field(default_factory=DesignResult)
    generated_code: Dict[str, str] = field(default_factory=dict)
    generated_tests: Dict[str, str] = field(default_factory=dict)
    validation: ValidationResult = field(default_factory=ValidationResult)
    summary: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    @property
    def functional_requirements(self) -> List[Requirement]:
        return self.requirements.functional_requirements

    @functional_requirements.setter
    def functional_requirements(self, val: List[Requirement]) -> None:
        self.requirements.functional_requirements = val

    @property
    def non_functional_requirements(self) -> List[Requirement]:
        return self.requirements.non_functional_requirements

    @property
    def assumptions(self) -> List[Requirement]:
        return self.requirements.assumptions

    @property
    def risks(self) -> List[Requirement]:
        return self.requirements.risks

    @property
    def validation_report(self) -> Dict[str, Any]:
        return {"status": self.validation.status, "summary": self.validation.summary, "checks": self.validation.checks}
