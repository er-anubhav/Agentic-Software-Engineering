from abc import ABC
import logging

from config.llm import get_llm
from tools.json_parser import parse_llm_json


logging.basicConfig(level=logging.INFO)


class BaseAgent(ABC):
    """
    Base class for all engineering agents.
    Provides:
    - Shared LLM instance
    - JSON parsing
    - Logging
    """

    def __init__(self):
        self.llm = get_llm()
        self.logger = logging.getLogger(self.__class__.__name__)

    def invoke(self, prompt: str) -> str:
        """
        Invoke the LLM and return raw text.
        """
        self.logger.info("Invoking LLM...")
        response = self.llm.invoke(prompt)
        return response.content

    def invoke_json(self, prompt: str) -> dict:
        """
        Invoke the LLM and return parsed JSON.
        """
        content = self.invoke(prompt)
        return parse_llm_json(content)