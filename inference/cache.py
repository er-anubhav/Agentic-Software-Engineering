import hashlib
import time
from typing import Dict, Any, Optional
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field

from inference.provider import LLMResponse


class CacheEntry(BaseModel):
    key: str
    response: LLMResponse
    created_at: float = Field(default_factory=time.time)


class PromptCache:
    """
    SHA-256 Prompt Hashing and Completion Cache.
    """

    def __init__(self, ttl_seconds: int = 3600):
        self.ttl_seconds = ttl_seconds
        self.cache: Dict[str, CacheEntry] = {}
        self.hits: int = 0
        self.misses: int = 0

    def compute_key(self, prompt: str, model: str) -> str:
        raw = f"{model}:{prompt}".encode("utf-8")
        return hashlib.sha256(raw).hexdigest()

    def get(self, prompt: str, model: str) -> Optional[LLMResponse]:
        key = self.compute_key(prompt, model)
        entry = self.cache.get(key)
        if entry:
            if time.time() - entry.created_at < self.ttl_seconds:
                self.hits += 1
                resp = entry.response.model_copy()
                resp.cache_hit = True
                return resp
            else:
                del self.cache[key]
        self.misses += 1
        return None

    def set(self, prompt: str, model: str, response: LLMResponse) -> None:
        key = self.compute_key(prompt, model)
        self.cache[key] = CacheEntry(key=key, response=response)

    def clear(self) -> None:
        self.cache.clear()
        self.hits = 0
        self.misses = 0
