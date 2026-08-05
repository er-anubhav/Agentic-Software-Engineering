import time
from typing import Dict, Any, Optional
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field


class RateLimitConfig(BaseModel):
    rpm: int = 600      # Requests per minute
    tpm: int = 100000   # Tokens per minute
    burst: int = 50


class ProviderRateLimiter:
    """
    Token-bucket rate limiter enforcing RPM and TPM limits per provider.
    """

    def __init__(self):
        self.configs: Dict[str, RateLimitConfig] = {
            "openai": RateLimitConfig(rpm=600, tpm=100000),
            "anthropic": RateLimitConfig(rpm=300, tpm=80000),
            "gemini": RateLimitConfig(rpm=1000, tpm=200000),
            "openrouter": RateLimitConfig(rpm=500, tpm=150000),
            "ollama": RateLimitConfig(rpm=10000, tpm=1000000),
            "vllm": RateLimitConfig(rpm=10000, tpm=1000000),
            "azure_openai": RateLimitConfig(rpm=600, tpm=100000)
        }
        self.request_counts: Dict[str, int] = {}
        self.last_reset: Dict[str, float] = {}

    def check_and_increment(self, provider: str, prompt_tokens: int = 100) -> bool:
        now = time.time()
        if provider not in self.last_reset or now - self.last_reset[provider] > 60.0:
            self.request_counts[provider] = 0
            self.last_reset[provider] = now

        cfg = self.configs.get(provider, RateLimitConfig())
        if self.request_counts[provider] >= cfg.rpm:
            return False  # Rate limit exceeded

        self.request_counts[provider] += 1
        return True
