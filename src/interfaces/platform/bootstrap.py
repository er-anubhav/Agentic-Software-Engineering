"""
src/platform/bootstrap.py — Layer 0: System Bootstrapper & Dependency Injection Resolver.

Decouples service instantiation from the DI Container.
"""
import logging
from src.core.config import get_settings, Settings
from src.core.container import get_container, Container
from src.infrastructure.storage.persistence.sqlite_store import SQLiteStore
from src.infrastructure.storage.persistence.base_store import RelationalStore
from src.infrastructure.inference.gateway import UnifiedInferenceGateway

logger = logging.getLogger(__name__)


def bootstrap_system() -> Container:
    """
    Builds and registers core platform services into the DI Container.
    """
    settings = get_settings()
    container = get_container()

    # 1. Register Relational Storage Service
    sqlite_store = SQLiteStore(db_path=settings.repository_path + "/platform.db")
    container.register(RelationalStore, sqlite_store)

    # 2. Register Unified LLM Gateway Service
    gateway = UnifiedInferenceGateway.get_instance()
    container.register(UnifiedInferenceGateway, gateway)

    logger.info("System bootstrap complete. Services registered in DI Container.")
    return container
