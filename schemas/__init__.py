from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class RequirementItem(BaseModel):
    id: str
    description: str


class RequirementAnalysisSchema(BaseModel):
    functional_requirements: List[str] = Field(default_factory=list, description="List of functional requirements")
    non_functional_requirements: List[str] = Field(default_factory=list, description="List of non-functional requirements")
    assumptions: List[str] = Field(default_factory=list, description="List of assumptions")
    ambiguities: List[str] = Field(default_factory=list, description="List of ambiguities")
    risks: List[str] = Field(default_factory=list, description="List of technical/project risks")


class PlannerSchema(BaseModel):
    tasks: List[str] = Field(default_factory=list, description="Ordered implementation tasks")


class ArchitectureComponent(BaseModel):
    name: str
    responsibility: str


class ArchitectureSchema(BaseModel):
    architecture_style: str = Field(default="Monolithic / Microservices")
    components: List[ArchitectureComponent] = Field(default_factory=list)
    communication: List[Dict[str, str]] = Field(default_factory=list)
    data_flow: List[str] = Field(default_factory=list)


class ModuleDesign(BaseModel):
    name: str
    responsibility: str


class APIDesign(BaseModel):
    name: str
    method: str
    path: str


class DatabaseDesign(BaseModel):
    table: str
    purpose: str


class DesignSchema(BaseModel):
    modules: List[ModuleDesign] = Field(default_factory=list)
    apis: List[APIDesign] = Field(default_factory=list)
    database: List[DatabaseDesign] = Field(default_factory=list)


class ValidationCheck(BaseModel):
    artifact: str
    status: str
    message: str


class ValidationSchema(BaseModel):
    status: str = Field(description="PASS, PASS_WITH_WARNINGS, or FAIL")
    checks: List[ValidationCheck] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    summary: str = Field(default="")
