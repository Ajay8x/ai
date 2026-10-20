"""
AJAX AI - Plugin Architecture & Base Classes
Enables modular, sandboxed, and permission-controlled plugin extensions.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from tools.base import BaseTool

@dataclass
class PluginManifest:
    name: str
    version: str
    description: str
    author: str = "AJAX Developer"
    permissions: List[str] = field(default_factory=lambda: ["SAFE"])
    enabled: bool = True
    config: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PluginManifest":
        return cls(
            name=data.get("name", "UnnamedPlugin"),
            version=data.get("version", "1.0.0"),
            description=data.get("description", ""),
            author=data.get("author", "AJAX Developer"),
            permissions=data.get("permissions", ["SAFE"]),
            enabled=data.get("enabled", True),
            config=data.get("config", {})
        )

class BasePlugin(ABC):
    """Abstract base class for all AJAX AI plugins."""
    def __init__(self, manifest: PluginManifest):
        self.manifest = manifest
        self.is_active = False

    @abstractmethod
    def on_load(self) -> bool:
        """Called when the plugin is loaded into memory."""
        pass

    @abstractmethod
    def on_unload(self) -> bool:
        """Called when the plugin is unloaded."""
        pass

    def get_tools(self) -> List[BaseTool]:
        """Return list of Tool instances provided by this plugin."""
        return []

    def get_info(self) -> Dict[str, Any]:
        return {
            "name": self.manifest.name,
            "version": self.manifest.version,
            "description": self.manifest.description,
            "author": self.manifest.author,
            "permissions": self.manifest.permissions,
            "is_active": self.is_active
        }
