import json
from typing import Type, TypeVar, Optional, Callable, Any
# pyrefly: ignore [missing-import]
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class StructuredOutputParser:
    """
    Parses LLM text outputs into Pydantic models with validation, retries, and fallback.
    """

    @staticmethod
    def parse_or_fallback(
        text: str,
        model_class: Type[T],
        fallback_factory: Optional[Callable[[], T]] = None
    ) -> T:
        try:
            # Try direct JSON parsing
            clean_text = text
            if "```json" in text:
                clean_text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                clean_text = text.split("```")[1].split("```")[0].strip()

            data = json.loads(clean_text)
            return model_class.model_validate(data)
        except Exception:
            if fallback_factory:
                return fallback_factory()
            # Default instantiation fallback
            try:
                return model_class()
            except Exception as e:
                raise ValueError(f"Failed to parse or construct fallback for model {model_class.__name__}: {str(e)}")
