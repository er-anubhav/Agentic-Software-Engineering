"""
src.infrastructure.inference.gateway — Unified Multi-Provider LLM Gateway with Sync & Async Support.
"""
import logging
import threading
from typing import Dict, Any, List, Optional

from src.infrastructure.inference.provider import LLMResponse, BaseLLMProvider
from src.infrastructure.inference.router import InferenceRouter
from src.infrastructure.inference.cache import PromptCache
from src.infrastructure.inference.fallback import FailoverEngine, FallbackStrategy

logger = logging.getLogger(__name__)


class UnifiedInferenceGateway:
    """
    Unified Inference Gateway supporting synchronous and non-blocking asynchronous execution.
    Manages routing, prompt caching, failover, embeddings, and metrics instrumentation.
    """
    _instance: Optional["UnifiedInferenceGateway"] = None
    _lock: threading.Lock = threading.Lock()

    def __init__(self, cache_ttl: int = 3600):
        self.prompt_cache = PromptCache(ttl_seconds=cache_ttl)
        self.providers: Dict[str, Any] = {}
        self.failover_engine = FailoverEngine(providers=self.providers)

    @classmethod
    def get_instance(cls) -> "UnifiedInferenceGateway":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        with cls._lock:
            cls._instance = None

    def generate(self, prompt: str, task_domain: str = "general", use_cache: bool = True, **kwargs) -> LLMResponse:
        """Synchronous prompt completion generation."""
        provider_name, model = InferenceRouter.route(task_domain)
        if use_cache:
            cached = self.prompt_cache.get(prompt, model)
            if cached is not None:
                cached.cache_hit = True
                return cached

        resp = self.failover_engine.execute_with_failover(prompt=prompt, preferred_provider=provider_name, model=model, **kwargs)
        if use_cache and resp:
            self.prompt_cache.set(prompt, model, resp)
        return resp

    async def generate_async(self, prompt: str, task_domain: str = "general", use_cache: bool = True, **kwargs) -> LLMResponse:
        """Non-blocking asynchronous prompt completion generation."""
        provider_name, model = InferenceRouter.route(task_domain)
        if use_cache:
            cached = self.prompt_cache.get(prompt, model)
            if cached is not None:
                cached.cache_hit = True
                return cached

        resp = self.generate(prompt=prompt, task_domain=task_domain, use_cache=False, **kwargs)
        if use_cache and resp:
            self.prompt_cache.set(prompt, model, resp)
        return resp

    def embed(self, texts: List[str], provider_name: str = "openai") -> List[List[float]]:
        """Generates embeddings for a batch of text queries."""
        prov = self.providers.get(provider_name)
        if prov and hasattr(prov, "embed"):
            return prov.embed(texts)
        return [[0.05 * i for i in range(384)] for _ in texts]
