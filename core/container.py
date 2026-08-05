from core.config import get_settings, Settings
from config.llm import get_llm


class Container:
    """
    Lightweight Dependency Injection container.
    """
    _instance = None

    def __init__(self):
        self.settings: Settings = get_settings()
        self._llm = None

    @classmethod
    def get_instance(cls) -> "Container":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def get_llm(self):
        if self._llm is None:
            self._llm = get_llm()
        return self._llm


def get_container() -> Container:
    return Container.get_instance()
