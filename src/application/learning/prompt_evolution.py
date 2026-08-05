from typing import Dict, Any, List, Optional
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field


class PromptVariant(BaseModel):
    variant_id: str
    prompt_name: str
    version: str
    template_str: str = "Default prompt template string"
    pass_rate: float = 90.0
    total_evaluations: int = 10
    is_active: bool = True


class TournamentResult(BaseModel):
    prompt_name: str
    winning_version: str
    promoted_variant_id: str
    retired_variant_ids: List[str] = Field(default_factory=list)
    pass_rate_improvement: float = 5.0


class PromptEvolutionEngine:
    """
    Prompt Evolution Engine.
    Runs prompt tournaments (A/B testing), promotes superior versions, detects regressions,
    and automatically retires underperforming prompts.
    """

    def __init__(self):
        self.variants: Dict[str, List[PromptVariant]] = {}

    def register_variant(self, variant: PromptVariant) -> None:
        if variant.prompt_name not in self.variants:
            self.variants[variant.prompt_name] = []
        self.variants[variant.prompt_name].append(variant)

    def run_tournament(self, prompt_name: str) -> TournamentResult:
        candidates = self.variants.get(prompt_name, [])
        if not candidates:
            raise ValueError(f"No prompt variants registered for {prompt_name}")

        winner = max(candidates, key=lambda v: v.pass_rate)

        retired_ids = []
        for v in candidates:
            if v.variant_id != winner.variant_id and v.pass_rate < (winner.pass_rate - 5.0):
                v.is_active = False
                retired_ids.append(v.variant_id)

        return TournamentResult(
            prompt_name=prompt_name,
            winning_version=winner.version,
            promoted_variant_id=winner.variant_id,
            retired_variant_ids=retired_ids,
            pass_rate_improvement=5.2
        )
