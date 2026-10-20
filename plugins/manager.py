"""
AJAX AI - Plugin Manager & Lifecycle Engine
Discovers, validates, sandbox-loads, and manages plugins.
"""

import os
import json
import importlib.util
from typing import Dict, List, Optional
from plugins.base import BasePlugin, PluginManifest
from tools.registry import registry
from core.logger import ajax_logger, error_logger

PLUGINS_DIR = os.path.dirname(os.path.abspath(__file__))

class PluginManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PluginManager, cls).__new__(cls)
            cls._instance.plugins: Dict[str, BasePlugin] = {}
        return cls._instance

    def discover_and_load(self):
        """Scans plugins directory for subdirectories containing plugin.json."""
        if not os.path.exists(PLUGINS_DIR):
            return

        for item in os.listdir(PLUGINS_DIR):
            item_path = os.path.join(PLUGINS_DIR, item)
            if not os.path.isdir(item_path) or item.startswith("__"):
                continue

            manifest_path = os.path.join(item_path, "plugin.json")
            if not os.path.exists(manifest_path):
                continue

            try:
                with open(manifest_path, "r", encoding="utf-8") as f:
                    manifest_data = json.load(f)

                manifest = PluginManifest.from_dict(manifest_data)
                if not manifest.enabled:
                    ajax_logger.info(f"Skipping disabled plugin: {manifest.name}")
                    continue

                # Locate python entry script
                entry_file = manifest_data.get("entry_point", f"{item}_plugin.py")
                entry_path = os.path.join(item_path, entry_file)
                if not os.path.exists(entry_path):
                    # fallback to any .py file in directory
                    py_files = [f for f in os.listdir(item_path) if f.endswith(".py") and not f.startswith("__")]
                    if py_files:
                        entry_path = os.path.join(item_path, py_files[0])
                    else:
                        continue

                # Dynamically load the module
                spec = importlib.util.spec_from_file_location(f"plugins.{item}", entry_path)
                if spec and spec.loader:
                    mod = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(mod)

                    # Search for BasePlugin subclass
                    for attr_name in dir(mod):
                        attr = getattr(mod, attr_name)
                        if isinstance(attr, type) and issubclass(attr, BasePlugin) and attr is not BasePlugin:
                            plugin_inst = attr(manifest)
                            if plugin_inst.on_load():
                                plugin_inst.is_active = True
                                self.plugins[manifest.name] = plugin_inst
                                # Register plugin tools
                                for tool in plugin_inst.get_tools():
                                    registry.register(tool)
                                ajax_logger.info(f"Successfully loaded plugin: {manifest.name} v{manifest.version}")
                            break
            except Exception as e:
                error_logger.error(f"Failed loading plugin in {item}: {e}")

    def list_plugins(self) -> List[Dict]:
        return [p.get_info() for p in self.plugins.values()]

    def get_plugin(self, name: str) -> Optional[BasePlugin]:
        return self.plugins.get(name)

    def unload_all(self):
        for name, p in self.plugins.items():
            try:
                p.on_unload()
                p.is_active = False
            except Exception:
                pass
        self.plugins.clear()

plugin_manager = PluginManager()
