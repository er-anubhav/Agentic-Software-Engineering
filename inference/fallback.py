from typing import Dict, Any, List, Optional, Callable
from inference.provider import LLMProvider, LLMResponse


class FailoverEngine:
    """
    Automatic multi-provider failover sequence:
    OpenAI -> Anthropic -> Gemini -> OpenRouter -> Ollama -> vLLM -> Azure OpenAI
    """

    def __init__(self, providers: Dict[str, LLMProvider]):
        self.providers = providers
        self.default_cascade = ["openai", "anthropic", "gemini", "openrouter", "ollama", "vllm", "azure_openai"]

    def execute_with_failover(
        self,
        prompt: str,
        preferred_provider: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        cascade_override: Optional[List[str]] = None
    ) -> LLMResponse:
        cascade = cascade_override or self.default_cascade
        if preferred_provider and preferred_provider in cascade:
            # Reorder cascade to start with preferred provider
            cascade = [preferred_provider] + [p for p in cascade if p != preferred_provider]

        last_error = None
        for provider_name in cascade:
            provider = self.providers.get(provider_name)
            if not provider:
                continue

            try:
                if not provider.health():
                    continue

                response = provider.generate(prompt=prompt, model=model, max_tokens=max_tokens, temperature=temperature)
                return response
            except Exception as e:
                last_error = e
                continue

        raise RuntimeError(f"All LLM providers failed in failover cascade: {str(last_error)}")
