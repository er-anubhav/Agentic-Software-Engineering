import time
from typing import Callable, Any, Optional
# pyrefly: ignore [missing-import]
from pydantic import BaseModel


class ReasoningRetryPolicy(BaseModel):
    max_retries: int = 3
    backoff_factor: float = 1.5

    def execute_with_retry(self, func: Callable[[], Any], fallback_factory: Optional[Callable[[], Any]] = None) -> Any:
        last_exception = None
        for attempt in range(1, self.max_retries + 1):
            try:
                return func()
            except Exception as e:
                last_exception = e
                time.sleep(0.01 * (self.backoff_factor ** attempt))

        if fallback_factory:
            return fallback_factory()
        raise last_exception or RuntimeError("Execution failed after max retries.")
