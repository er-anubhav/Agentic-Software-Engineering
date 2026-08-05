from abc import ABC
import logging
from typing import Type, TypeVar, Optional
from pydantic import BaseModel

from src.core.container import get_container
from src.application.tools.json_parser import parse_llm_json

T = TypeVar("T", bound=BaseModel)

logging.basicConfig(level=logging.INFO)


class BaseAgent(ABC):
    """
    Base class for all engineering agents.
    Provides:
    - Shared LLM instance
    - Pydantic structured output validation
    - Fallback JSON parsing
    - Logging
    """

    def __init__(self):
        self.llm = get_container().get_llm()
        self.logger = logging.getLogger(self.__class__.__name__)

    def invoke(self, prompt: str) -> str:
        """
        Invoke the LLM and return raw text.
        """
        self.logger.info(f"[{self.__class__.__name__}] Invoking LLM...")
        response = self.llm.invoke(prompt)
        return response.content if hasattr(response, "content") else str(response)

    def invoke_json(self, prompt: str) -> dict:
        """
        Invoke the LLM and return parsed JSON.
        """
        content = self.invoke(prompt)
        return parse_llm_json(content)

    def invoke_structured(self, prompt: str, schema_class: Type[T]) -> T:
        """
        Invoke the LLM and return a validated Pydantic model instance.
        Uses structured output API with fallback parsing if needed.
        """
        try:
            if hasattr(self.llm, "with_structured_output"):
                structured_llm = self.llm.with_structured_output(schema_class)
                result = structured_llm.invoke(prompt)
                if isinstance(result, schema_class):
                    return result
                elif isinstance(result, dict):
                    return schema_class.model_validate(result)
        except Exception as e:
            self.logger.warning(f"Structured output API failed, using fallback parser: {e}")

        # Fallback parsing via JSON parser
        parsed_dict = self.invoke_json(prompt)
        return schema_class.model_validate(parsed_dict)