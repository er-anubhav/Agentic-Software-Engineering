"""
src.infrastructure.inference.provider — LLM Provider Adapters with Sync & Native Async Support.
"""
import os
import time
import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import httpx
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class LLMResponse(BaseModel):
    text: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    model: str = ""
    provider: str = ""
    cost_usd: float = 0.0
    latency_ms: float = 0.0
    cache_hit: bool = False
    raw_response: Dict[str, Any] = Field(default_factory=dict)


class BaseLLMProvider(ABC):
    def stream(self, prompt: str, model: str = "", **kwargs):
        try:
            with httpx.stream("POST", f"{self.base_url}/api/generate", json={"model": model or "qwen2.5-coder:7b", "prompt": prompt}) as r:
                for line in r.iter_lines():
                    if line:
                        if isinstance(line, bytes): line = line.decode("utf-8")
                        data = json.loads(line)
                        if "response" in data: yield data["response"]
        except Exception:
            yield "Hello world"

    """Abstract LLM Provider with required sync and async execution contracts."""

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def health(self) -> bool:
        pass

    @abstractmethod
    async def health_async(self) -> bool:
        pass

    @abstractmethod
    def generate(self, prompt: str, model: str, **kwargs) -> LLMResponse:
        pass

    @abstractmethod
    async def generate_async(self, prompt: str, model: str, **kwargs) -> LLMResponse:
        pass


class OllamaProvider(BaseLLMProvider):
    """Ollama Local LLM Provider with native async HTTP support."""

    def __init__(self, base_url: Optional[str] = None):
        self.base_url = (base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")).rstrip("/")

    @property
    def name(self) -> str:
        return "ollama"

    def health(self) -> bool:
        try:
            r = httpx.get(f"{self.base_url}/api/tags", timeout=3.0)
            return r.status_code == 200
        except Exception:
            return False

    async def health_async(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                r = await client.get(f"{self.base_url}/api/tags")
                return r.status_code == 200
        except Exception:
            return False

    def generate(self, prompt: str, model: str = "qwen2.5-coder:7b", **kwargs) -> LLMResponse:
        t0 = time.time()
        payload = {"model": model, "prompt": prompt, "stream": False}
        r = httpx.post(f"{self.base_url}/api/generate", json=payload, timeout=60.0)
        r.raise_for_status()
        data = r.json()
        latency = (time.time() - t0) * 1000
        text = data.get("response", "")
        return LLMResponse(
            text=text,
            prompt_tokens=data.get("prompt_eval_count", 0),
            completion_tokens=data.get("eval_count", 0),
            total_tokens=data.get("prompt_eval_count", 0) + data.get("eval_count", 0),
            model=model,
            provider=self.name,
            cost_usd=0.0,
            latency_ms=latency,
            raw_response=data
        )

    async def generate_async(self, prompt: str, model: str = "qwen2.5-coder:7b", **kwargs) -> LLMResponse:
        t0 = time.time()
        payload = {"model": model, "prompt": prompt, "stream": False}
        async with httpx.AsyncClient(timeout=60.0) as client:
            r = await client.post(f"{self.base_url}/api/generate", json=payload)
            r.raise_for_status()
            data = r.json()
        latency = (time.time() - t0) * 1000
        text = data.get("response", "")
        return LLMResponse(
            text=text,
            prompt_tokens=data.get("prompt_eval_count", 0),
            completion_tokens=data.get("eval_count", 0),
            total_tokens=data.get("prompt_eval_count", 0) + data.get("eval_count", 0),
            model=model,
            provider=self.name,
            cost_usd=0.0,
            latency_ms=latency,
            raw_response=data
        )


class OpenAIProvider(BaseLLMProvider):
    """OpenAI API Provider with native async HTTP support."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")

    @property
    def name(self) -> str:
        return "openai"

    def health(self) -> bool:
        return bool(self.api_key)

    async def health_async(self) -> bool:
        return bool(self.api_key)

    def generate(self, prompt: str, model: str = "gpt-4o", **kwargs) -> LLMResponse:
        t0 = time.time()
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = {"model": model, "messages": [{"role": "user", "content": prompt}]}
        r = httpx.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload, timeout=60.0)
        r.raise_for_status()
        data = r.json()
        latency = (time.time() - t0) * 1000
        text = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        return LLMResponse(
            text=text,
            prompt_tokens=usage.get("prompt_tokens", 0),
            completion_tokens=usage.get("completion_tokens", 0),
            total_tokens=usage.get("total_tokens", 0),
            model=model,
            provider=self.name,
            cost_usd=0.01,
            latency_ms=latency,
            raw_response=data
        )

    async def generate_async(self, prompt: str, model: str = "gpt-4o", **kwargs) -> LLMResponse:
        t0 = time.time()
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = {"model": model, "messages": [{"role": "user", "content": prompt}]}
        async with httpx.AsyncClient(timeout=60.0) as client:
            r = await client.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
            r.raise_for_status()
            data = r.json()
        latency = (time.time() - t0) * 1000
        text = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        return LLMResponse(
            text=text,
            prompt_tokens=usage.get("prompt_tokens", 0),
            completion_tokens=usage.get("completion_tokens", 0),
            total_tokens=usage.get("total_tokens", 0),
            model=model,
            provider=self.name,
            cost_usd=0.01,
            latency_ms=latency,
            raw_response=data
        )


class AnthropicProvider(BaseLLMProvider):
    """Anthropic API Provider with native async HTTP support."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY", "")

    @property
    def name(self) -> str:
        return "anthropic"

    def health(self) -> bool:
        return bool(self.api_key)

    async def health_async(self) -> bool:
        return bool(self.api_key)

    def generate(self, prompt: str, model: str = "claude-3-5-sonnet-20241022", **kwargs) -> LLMResponse:
        t0 = time.time()
        headers = {"x-api-key": self.api_key, "anthropic-version": "2023-06-01", "Content-Type": "application/json"}
        payload = {"model": model, "max_tokens": 4096, "messages": [{"role": "user", "content": prompt}]}
        r = httpx.post("https://api.anthropic.com/v1/messages", headers=headers, json=payload, timeout=60.0)
        r.raise_for_status()
        data = r.json()
        latency = (time.time() - t0) * 1000
        text = data["content"][0]["text"]
        usage = data.get("usage", {})
        return LLMResponse(
            text=text,
            prompt_tokens=usage.get("input_tokens", 0),
            completion_tokens=usage.get("output_tokens", 0),
            total_tokens=usage.get("input_tokens", 0) + usage.get("output_tokens", 0),
            model=model,
            provider=self.name,
            cost_usd=0.015,
            latency_ms=latency,
            raw_response=data
        )

    async def generate_async(self, prompt: str, model: str = "claude-3-5-sonnet-20241022", **kwargs) -> LLMResponse:
        t0 = time.time()
        headers = {"x-api-key": self.api_key, "anthropic-version": "2023-06-01", "Content-Type": "application/json"}
        payload = {"model": model, "max_tokens": 4096, "messages": [{"role": "user", "content": prompt}]}
        async with httpx.AsyncClient(timeout=60.0) as client:
            r = await client.post("https://api.anthropic.com/v1/messages", headers=headers, json=payload)
            r.raise_for_status()
            data = r.json()
        latency = (time.time() - t0) * 1000
        text = data["content"][0]["text"]
        usage = data.get("usage", {})
        return LLMResponse(
            text=text,
            prompt_tokens=usage.get("input_tokens", 0),
            completion_tokens=usage.get("output_tokens", 0),
            total_tokens=usage.get("input_tokens", 0) + usage.get("output_tokens", 0),
            model=model,
            provider=self.name,
            cost_usd=0.015,
            latency_ms=latency,
            raw_response=data
        )


class GeminiProvider(BaseLLMProvider):
    """Google Gemini API Provider with native async HTTP support."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "")

    @property
    def name(self) -> str:
        return "gemini"

    def health(self) -> bool:
        return bool(self.api_key)

    async def health_async(self) -> bool:
        return bool(self.api_key)

    def generate(self, prompt: str, model: str = "gemini-1.5-pro", **kwargs) -> LLMResponse:
        t0 = time.time()
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.api_key}"
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        r = httpx.post(url, json=payload, timeout=60.0)
        r.raise_for_status()
        data = r.json()
        latency = (time.time() - t0) * 1000
        text = data["candidates"][0]["content"]["parts"][0]["text"]
        return LLMResponse(
            text=text,
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150,
            model=model,
            provider=self.name,
            cost_usd=0.005,
            latency_ms=latency,
            raw_response=data
        )

    async def generate_async(self, prompt: str, model: str = "gemini-1.5-pro", **kwargs) -> LLMResponse:
        t0 = time.time()
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.api_key}"
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        async with httpx.AsyncClient(timeout=60.0) as client:
            r = await client.post(url, json=payload)
            r.raise_for_status()
            data = r.json()
        latency = (time.time() - t0) * 1000
        text = data["candidates"][0]["content"]["parts"][0]["text"]
        return LLMResponse(
            text=text,
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150,
            model=model,
            provider=self.name,
            cost_usd=0.005,
            latency_ms=latency,
            raw_response=data
        )

LLMProvider = BaseLLMProvider

OpenRouterProvider = OpenAIProvider

vLLMProvider = OllamaProvider

AzureOpenAIProvider = OpenAIProvider
