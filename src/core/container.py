"""
src.core.container — Layer 0: Pure Type-Based Dependency Injection Container.
"""
import logging
import threading
from typing import Dict, Any, Type, TypeVar, Optional
from src.core.config import get_settings, Settings

logger = logging.getLogger(__name__)
T = TypeVar("T")


class Container:
    """
    Pure Thread-Safe Dependency Injection Container & Service Locator.
    Strictly type-based registry with zero string matching or dynamic module tricks.
    """
    _instance: Optional["Container"] = None
    _lock: threading.Lock = threading.Lock()

    def __init__(self):
        self.settings: Settings = get_settings()
        self._services: Dict[Type[Any], Any] = {}

    @classmethod
    def get_instance(cls) -> "Container":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Reset singleton for clean test isolation."""
        with cls._lock:
            cls._instance = None

    def register(self, service_type: Type[T], instance: T) -> None:
        """Register a service instance bound to its interface or class type."""
        with self._lock:
            self._services[service_type] = instance
            logger.debug("Registered service type '%s' in DI container.", service_type.__name__)

    def resolve(self, service_type: Type[T]) -> T:
        """Resolve a service instance by its exact interface or class type."""
        with self._lock:
            if service_type in self._services:
                return self._services[service_type]
        raise KeyError(f"Service of type '{service_type.__name__}' is not registered in DI container.")

    def resolve_optional(self, service_type: Type[T]) -> Optional[T]:
        """Safely resolve a service instance, returning None if not registered."""
        with self._lock:
            return self._services.get(service_type)

    def get_llm(self) -> Any:
        """Helper resolving registered LLM Gateway service without upward imports."""
        with self._lock:
            for service_type, instance in self._services.items():
                if getattr(service_type, "__name__", "") == "UnifiedInferenceGateway":
                    return instance
        return None


def get_container() -> Container:
    return Container.get_instance()
