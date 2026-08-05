from dataclasses import dataclass, field
from typing import List, Dict, Any


@dataclass
class Requirement:
    id: str
    description: str


@dataclass
class EngineeringState:

    # ==========================================================
    # User Input
    # ==========================================================
    requirement: str = ""

    # ==========================================================
    # Requirement Analysis
    # ==========================================================
    functional_requirements: List[Requirement] = field(default_factory=list)
    non_functional_requirements: List[Requirement] = field(default_factory=list)
    assumptions: List[Requirement] = field(default_factory=list)
    ambiguities: List[Requirement] = field(default_factory=list)
    risks: List[Requirement] = field(default_factory=list)

    # ==========================================================
    # Planning
    # ==========================================================
    tasks: List[str] = field(default_factory=list)

    # ==========================================================
    # Architecture & Design
    # ==========================================================
    architecture: str = ""
    design: Dict[str, Any] = field(default_factory=dict)

    # ==========================================================
    # Execution Plan
    # ==========================================================
    execution_plan: Dict[str, Any] = field(default_factory=dict)

    # ==========================================================
    # Brownfield Analysis
    # ==========================================================
    repository_path: str = ""
    codebase_analysis: Dict[str, Any] = field(default_factory=dict)

    # ==========================================================
    # Engineering Artifacts
    # ==========================================================
    api_spec: Dict[str, Any] = field(default_factory=dict)
    database_schema: Dict[str, str] = field(default_factory=dict)

    # ==========================================================
    # Generated Source Code
    # ==========================================================
    generated_code: Dict[str, str] = field(default_factory=dict)

    # ==========================================================
    # Generated Tests
    # ==========================================================
    tests: Dict[str, str] = field(default_factory=dict)

    # ==========================================================
    # Validation
    # ==========================================================
    validation_report: Dict[str, Any] = field(default_factory=dict)

    # ==========================================================
    # Human Approval
    # ==========================================================
    approved: bool = False

    # ==========================================================
    # Engineering Summary
    # ==========================================================
    engineering_summary: Dict[str, Any] = field(default_factory=dict)

    # ==========================================================
    # Documentation
    # ==========================================================
    documentation: str = ""

    # ==========================================================
    # Metadata & Execution Status
    # ==========================================================
    metadata: Dict[str, Any] = field(default_factory=dict)
    context_snippets: List[str] = field(default_factory=list)
    execution_status: str = "COMPLETED"

    # ==========================================================
    # Final Summary
    # ==========================================================
    summary: str = ""