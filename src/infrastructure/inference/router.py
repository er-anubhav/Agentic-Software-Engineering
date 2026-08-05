from typing import Dict, Any, Optional


class InferenceRouter:
    """
    Intelligent routing mapping task domains to appropriate providers and model tiers.
    Task -> Model Mapping:
      - Retrieval -> Cheap (Gemini / Ollama)
      - Planning -> Medium (OpenAI / Anthropic)
      - Repair -> Large (OpenAI gpt-4o / Anthropic claude-3-5-sonnet)
      - Architecture -> Large (OpenAI gpt-4o / Anthropic claude-3-5-sonnet)
      - Evaluation -> Cheap (Gemini / Ollama)
      - Reflection -> Medium (Anthropic / Gemini)
    """

    TASK_ROUTING = {
        "retrieval": ("gemini", "gemini-1.5-pro"),
        "planning": ("openai", "gpt-4o"),
        "repair": ("anthropic", "claude-3-5-sonnet"),
        "architecture": ("openai", "gpt-4o"),
        "evaluation": ("gemini", "gemini-1.5-pro"),
        "reflection": ("anthropic", "claude-3-5-sonnet")
    }

    @classmethod
    def route(cls, task_domain: str) -> tuple[str, str]:
        domain_clean = task_domain.lower().strip()
        for key, route_val in cls.TASK_ROUTING.items():
            if key in domain_clean:
                return route_val
        return ("openai", "gpt-4o")  # Default route
