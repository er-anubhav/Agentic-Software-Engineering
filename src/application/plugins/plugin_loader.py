"""
src.application.plugins.plugin_loader — Dynamic Agent Plugin SDK & Manifest Loader.
"""
import os
import json
import logging
import importlib
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class AgentPluginManifest(BaseModel):
    """Manifest metadata contract for external community agent plugins."""
    name: str
    version: str = "1.0.0"
    description: str = ""
    author: str = ""
    entry_point: str  # e.g., "my_plugin.agent:CustomAgent"
    capabilities: List[str] = Field(default_factory=list)


class PluginLoader:
    """
    Dynamic Plugin Loader discovering external agent plugins via directory manifests or entry points.
    """
    def __init__(self, plugins_dir: Optional[str] = None):
        self.plugins_dir = plugins_dir or os.path.join(os.getcwd(), "plugins")
        self._loaded_plugins: Dict[str, Any] = {}

    def discover_and_load(self) -> Dict[str, Any]:
        """Discovers and registers external plugin manifests."""
        if not os.path.exists(self.plugins_dir):
            logger.debug("Plugins directory '%s' does not exist. Skipping plugin discovery.", self.plugins_dir)
            return self._loaded_plugins

        for item in os.listdir(self.plugins_dir):
            plugin_path = os.path.join(self.plugins_dir, item)
            manifest_file = os.path.join(plugin_path, "plugin.json")

            if os.path.isdir(plugin_path) and os.path.exists(manifest_file):
                try:
                    with open(manifest_file, "r") as f:
                        data = json.load(f)
                    manifest = AgentPluginManifest(**data)
                    agent_cls = self._import_entry_point(manifest.entry_point)
                    if agent_cls:
                        self._loaded_plugins[manifest.name] = agent_cls
                        logger.info("Loaded agent plugin '%s' (v%s)", manifest.name, manifest.version)
                except Exception as e:
                    logger.error("Failed to load plugin from '%s': %s", plugin_path, e, exc_info=True)

        return self._loaded_plugins

    def _import_entry_point(self, entry_point: str) -> Optional[Any]:
        try:
            module_name, class_name = entry_point.rsplit(":", 1)
            module = importlib.import_module(module_name)
            return getattr(module, class_name, None)
        except Exception as e:
            logger.error("Could not import entry point '%s': %s", entry_point, e)
            return None
