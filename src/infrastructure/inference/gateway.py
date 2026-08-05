from typing import Dict, Any, List, Optional, Generator, Type, TypeVar
# pyrefly: ignore [missing-import]
from pydantic import BaseModel

from src.infrastructure.inference.provider import (
    LLMProvider,
    LLMResponse,
    OpenAIProvider,
    AnthropicProvider,
    GeminiProvider,
    OpenRouterProvider,
    OllamaProvider,
    vLLMProvider,
    AzureOpenAIProvider
)
from src.infrastructure.inference.cache import PromptCache
from src.infrastructure.inference.cost_tracker import InferenceCostTracker
from src.infrastructure.inference.rate_limiter import ProviderRateLimiter
from src.infrastructure.inference.fallback import FailoverEngine
from src.infrastructure.inference.router import InferenceRouter
from src.infrastructure.inference.structured_output import StructuredOutputParser
from src.infrastructure.inference.streaming import InferenceStreamer

T = TypeVar("T", bound=BaseModel)


class UnifiedInferenceGateway:
    """
    Production Multi-Provider LLM Inference Gateway (RFC-011).
    Centralized Gateway owning all model interactions across the entire platform.
    Features:
      - Multi-provider support (OpenAI, Anthropic, Gemini, OpenRouter, Ollama, vLLM, Azure OpenAI)
      - Dynamic task routing & automatic failover cascade
      - SHA-256 prompt caching
      - Provider token-bucket rate limiting
      - Structured output parsing (Pydantic models)
      - Streaming completion generation
      - Cost, latency, token, and trace accounting
      - Unified embedding gateway
    """

    _instance: Optional["UnifiedInferenceGateway"] = None

    def __init__(self):
        self.providers: Dict[str, LLMProvider] = {
            "openai": OpenAIProvider(),
            "anthropic": AnthropicProvider(),
            "gemini": GeminiProvider(),
            "openrouter": OpenRouterProvider(),
            "ollama": OllamaProvider(),
            "vllm": vLLMProvider(),
            "azure_openai": AzureOpenAIProvider()
        }
        self.cache = PromptCache()
        self.cost_tracker = InferenceCostTracker()
        self.rate_limiter = ProviderRateLimiter()
        self.failover_engine = FailoverEngine(self.providers)
        self.router = InferenceRouter()

    _lock = __import__('threading').Lock()

    @classmethod
    def get_instance(cls) -> "UnifiedInferenceGateway":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def generate(
        self,
        prompt: str,
        task_domain: str = "planning",
        provider: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        use_cache: bool = True,
        trace_id: str = "trace_default"
    ) -> LLMResponse:
        # Step 1: Determine target provider and model via Router
        target_provider, target_model = self.router.route(task_domain)
        eff_provider = provider or target_provider
        eff_model = model or target_model

        # Step 2: Check SHA-256 Prompt Cache
        if use_cache:
            cached_resp = self.cache.get(prompt, eff_model)
            if cached_resp:
                self.cost_tracker.record_request(cached_resp, trace_id=trace_id)
                return cached_resp

        # Step 3: Rate Limiting Check
        if not self.rate_limiter.check_and_increment(eff_provider):
            # Fallback if primary provider rate limited
            eff_provider = "ollama"

        # Step 4: Execute Generation with Automatic Failover
        response = self.failover_engine.execute_with_failover(
            prompt=prompt,
            preferred_provider=eff_provider,
            model=eff_model,
            max_tokens=max_tokens,
            temperature=temperature
        )

        # Step 5: Save to Cache & Cost Accounting
        if use_cache:
            self.cache.set(prompt, eff_model, response)

        self.cost_tracker.record_request(response, trace_id=trace_id)
        return response

    def generate_structured(
        self,
        prompt: str,
        model_class: Type[T],
        task_domain: str = "planning",
        trace_id: str = "trace_default"
    ) -> T:
        resp = self.generate(prompt=prompt, task_domain=task_domain, trace_id=trace_id)
        return StructuredOutputParser.parse_or_fallback(resp.text, model_class)

    def stream(
        self,
        prompt: str,
        provider_name: str = "openai",
        model: str = "gpt-4o"
    ) -> Generator[str, None, None]:
        prov = self.providers.get(provider_name, self.providers["openai"])
        return InferenceStreamer.stream_completion(prov, prompt, model)

    def embed(
        self,
        texts: List[str],
        provider_name: str = "openai",
        model: Optional[str] = None
    ) -> List[List[float]]:
        prov = self.providers.get(provider_name, self.providers["openai"])
        return prov.embed(texts, model)

    def get_provider_health(self) -> Dict[str, bool]:
        return {name: prov.health() for name, prov in self.providers.items()}
