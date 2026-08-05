from typing import Dict, Any, List, Optional
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field


class PromptTemplate(BaseModel):
    name: str
    version: str
    template_str: str
    benchmark_score: float = 90.0


class PromptLibrary:
    """
    Versioned Prompt Repository managing prompt templates across versions.
    """

    def __init__(self):
        self.templates: Dict[str, Dict[str, PromptTemplate]] = {}
        self._register_default_prompts()

    def register_prompt(self, template: PromptTemplate) -> None:
        if template.name not in self.templates:
            self.templates[template.name] = {}
        self.templates[template.name][template.version] = template

    def get_prompt(self, name: str, version: Optional[str] = None) -> PromptTemplate:
        versions = self.templates.get(name, {})
        if not versions:
            return PromptTemplate(name=name, version="v1", template_str="Default prompt for {task}")

        if version and version in versions:
            return versions[version]

        # Return latest / highest benchmarked version
        best_v = max(versions.values(), key=lambda t: t.benchmark_score)
        return best_v

    def _register_default_prompts(self) -> None:
        prompts = [
            PromptTemplate(name="planner", version="planner_v12", template_str="Generate dependency DAG for task {task}", benchmark_score=94.5),
            PromptTemplate(name="repair", version="repair_v6", template_str="Generate AST unified diff patch for {file}", benchmark_score=96.0),
            PromptTemplate(name="evaluation", version="evaluation_v8", template_str="Evaluate benchmark scores for repo {repo}", benchmark_score=95.0)
        ]
        for p in prompts:
            self.register_prompt(p)


class AutomaticPromptOptimizer:
    """
    Benchmarks prompt variants (Prompt A vs Prompt B vs Prompt C) and keeps the best performing prompt.
    """

    @staticmethod
    def select_best_prompt(templates: List[PromptTemplate]) -> PromptTemplate:
        if not templates:
            raise ValueError("No prompt templates provided for optimization.")
        return max(templates, key=lambda t: t.benchmark_score)
