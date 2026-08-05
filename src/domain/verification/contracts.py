from typing import Dict, Any, List, Optional, Callable
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field


class PreCondition(BaseModel):
    name: str
    condition_expression: str
    passed: bool = True


class PostCondition(BaseModel):
    name: str
    condition_expression: str
    passed: bool = True


class Invariant(BaseModel):
    name: str
    invariant_expression: str
    passed: bool = True


class SafetyRule(BaseModel):
    rule_id: str
    rule_name: str
    passed: bool = True


class EngineeringContract(BaseModel):
    contract_id: str
    target_symbol: str
    pre_conditions: List[PreCondition] = Field(default_factory=list)
    post_conditions: List[PostCondition] = Field(default_factory=list)
    invariants: List[Invariant] = Field(default_factory=list)
    safety_rules: List[SafetyRule] = Field(default_factory=list)
    is_valid: bool = True

    def validate_all(self) -> bool:
        all_passed = (
            all(p.passed for p in self.pre_conditions) and
            all(p.passed for p in self.post_conditions) and
            all(inv.passed for inv in self.invariants) and
            all(r.passed for r in self.safety_rules)
        )
        self.is_valid = all_passed
        return all_passed
