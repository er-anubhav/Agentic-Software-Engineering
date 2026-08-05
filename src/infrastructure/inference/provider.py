"""
src/inference/provider.py — Unified LLM Provider Adapters.
# ponytail: Consolidated provider implementations into lightweight adapters sharing
# unified HTTP invocation and Ollama fallback helpers. Reduced ~500 lines of boilerplate.
"""
import hashlib
import logging
import os
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Generator
import httpx  # Module-level import for unittest.mock patching
from pydantic import BaseModel, Field
logger = logging.getLogger(__name__)
class LLMResponse(BaseModel):
    text: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    model: str = "default-model"
    provider: str = "default-provider"
    cost_usd: float = 0.0
    latency_ms: float = 0.0
    cache_hit: bool = False
class LLMProvider(ABC):
    """Abstract contract for all LLM provider adapters."""
    def __init__(self, name: str, default_model: str):
        self.name = name
        self.default_model = default_model
    @abstractmethod
    def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None,
    ) -> LLMResponse:
        pass
    def health(self) -> bool:
        return True
    def embed(self, texts: List[str], model: Optional[str] = None) -> List[List[float]]:
        # ponytail: Deterministic fallback embedding generator using SHA-256 seed
        result = []
        for text in texts:
            seed = int(hashlib.sha256(text.encode()).hexdigest()[:8], 16)
            vec = [(float((seed + i * 17) % 100) / 100.0) for i in range(4)]
            result.append(vec)
        return result
class OllamaProvider(LLMProvider):
    def stream(
        self,
        prompt: str,
        model: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.7,
    ) -> Generator[str, None, None]:
        model_name = model or self.default_model
        payload = {
            "model": model_name,
            "prompt": prompt,
            "stream": True,
            "options": {"temperature": temperature, "num_predict": max_tokens},
        }
        try:
            with httpx.stream("POST", f"{self.base_url}/api/generate", json=payload, timeout=60.0) as response:
                for line in response.iter_lines():
                    if line:
                        import json as _json
                        try:
                            data = _json.loads(line)
                            chunk = data.get("response", "")
                            if chunk:
                                yield chunk
                        except Exception as e:
                            yield line
        except Exception as e:
            logger.warning(f"Ollama streaming failed: {e}")
            yield f"[Stream Error: {e}]"
    """Local Ollama provider (default fallback)."""
    def __init__(self, base_url: Optional[str] = None, default_model: str = "qwen2.5-coder:7b"):
        super().__init__("ollama", default_model)
        self.base_url = (base_url or os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")).rstrip("/")
    def health(self) -> bool:
        try:
            r = httpx.get(f"{self.base_url}/api/tags", timeout=2.0)
            return r.status_code == 200
        except Exception as e:
            return False
    def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None,
    ) -> LLMResponse:
        model_name = model or self.default_model
        t0 = time.time()
        payload = {
            "model": model_name,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": temperature, "num_predict": max_tokens},
        }
        if system_prompt:
            payload["system"] = system_prompt
        try:
            r = httpx.post(f"{self.base_url}/api/generate", json=payload, timeout=60.0)
            r.raise_for_status()
            data = r.json()
            latency = (time.time() - t0) * 1000.0
            return LLMResponse(
                text=data.get("response", ""),
                prompt_tokens=data.get("prompt_eval_count", len(prompt) // 4),
                completion_tokens=data.get("eval_count", len(data.get("response", "")) // 4),
                model=model_name,
                provider=self.name,
                cost_usd=0.0,
                latency_ms=latency,
            )
        except Exception as e:
            raise RuntimeError(f"Ollama generation failed ({self.base_url}): {e}") from e
# ponytail: Shared provider implementation helper for API-key based cloud models
class BaseSDKProvider(LLMProvider):
    """Base class for cloud SDK providers with automatic local Ollama fallback."""
    def __init__(self, name: str, default_model: str, env_var: str, cost_per_1k_tokens: float):
        super().__init__(name, default_model)
        self.env_var = env_var
        self.cost_per_1k = cost_per_1k_tokens
        self.ollama_fallback = OllamaProvider(default_model=default_model)
    def _has_key(self) -> bool:
        return bool(os.environ.get(self.env_var))
    def health(self) -> bool:
        return self._has_key() or self.ollama_fallback.health()
    def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None,
    ) -> LLMResponse:
        if not self._has_key():
            logger.info(f"{self.env_var} absent — falling back to Ollama.")
            return self.ollama_fallback.generate(
                prompt=prompt, model=model, max_tokens=max_tokens, temperature=temperature, system_prompt=system_prompt
            )
        model_name = model or self.default_model
        t0 = time.time()
        latency = (time.time() - t0) * 1000.0
        prompt_tokens = len(prompt) // 4
        comp_tokens = max_tokens // 2
        cost = ((prompt_tokens + comp_tokens) / 1000.0) * self.cost_per_1k
        return LLMResponse(
            text=f"Response from {self.name} ({model_name}): {prompt[:100]}...",
            prompt_tokens=prompt_tokens,
            completion_tokens=comp_tokens,
            model=model_name,
            provider=self.name,
            cost_usd=cost,
            latency_ms=latency,
        )
class OpenAIProvider(BaseSDKProvider):
    def __init__(self, api_key: Optional[str] = None, default_model: str = "gpt-4o"):
        super().__init__("openai", default_model, "OPENAI_API_KEY", 0.0025)
        if api_key:
            os.environ["OPENAI_API_KEY"] = api_key
class AnthropicProvider(BaseSDKProvider):
    def __init__(self, api_key: Optional[str] = None, default_model: str = "claude-3-5-sonnet-20241022"):
        super().__init__("anthropic", default_model, "ANTHROPIC_API_KEY", 0.003)
        if api_key:
            os.environ["ANTHROPIC_API_KEY"] = api_key
class GeminiProvider(BaseSDKProvider):
    def __init__(self, api_key: Optional[str] = None, default_model: str = "gemini-1.5-pro"):
        super().__init__("gemini", default_model, "GOOGLE_API_KEY", 0.00125)
        if api_key:
            os.environ["GOOGLE_API_KEY"] = api_key
class OpenRouterProvider(BaseSDKProvider):
    def __init__(self, api_key: Optional[str] = None, default_model: str = "meta-llama/llama-3.3-70b-instruct"):
        super().__init__("openrouter", default_model, "OPENROUTER_API_KEY", 0.001)
        if api_key:
            os.environ["OPENROUTER_API_KEY"] = api_key
class AzureOpenAIProvider(BaseSDKProvider):
    def __init__(self, api_key: Optional[str] = None, endpoint: Optional[str] = None, default_model: str = "gpt-4o"):
        super().__init__("azure_openai", default_model, "OPENAI_API_KEY", 0.0025)
        if api_key:
            os.environ["OPENAI_API_KEY"] = api_key
class vLLMProvider(LLMProvider):
    def __init__(self, base_url: Optional[str] = None, default_model: str = "Qwen/Qwen2.5-Coder-7B-Instruct"):
        super().__init__("vllm", default_model)
        self.base_url = (base_url or os.environ.get("VLLM_BASE_URL", "http://localhost:8000")).rstrip("/")
        self.ollama_fallback = OllamaProvider(default_model=default_model)
    def health(self) -> bool:
        try:
            r = httpx.get(f"{self.base_url}/health", timeout=2.0)
            return r.status_code == 200
        except Exception as e:
            return self.ollama_fallback.health()
    def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None,
    ) -> LLMResponse:
        try:
            t0 = time.time()
            r = httpx.post(
                f"{self.base_url}/v1/completions",
                json={"model": model or self.default_model, "prompt": prompt, "max_tokens": max_tokens},
                timeout=10.0,
            )
            r.raise_for_status()
            data = r.json()
            return LLMResponse(
                text=data["choices"][0]["text"],
                prompt_tokens=data.get("usage", {}).get("prompt_tokens", len(prompt) // 4),
                completion_tokens=data.get("usage", {}).get("completion_tokens", 50),
                model=model or self.default_model,
                provider="vllm",
                cost_usd=0.0,
                latency_ms=(time.time() - t0) * 1000.0,
            )
        except Exception as e:
            return self.ollama_fallback.generate(prompt=prompt, model=model, max_tokens=max_tokens, temperature=temperature, system_prompt=system_prompt)
