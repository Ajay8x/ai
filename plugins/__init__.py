"""
AJAX AI - Plugins Package
"""
from plugins.base import BasePlugin, PluginManifest
from plugins.manager import plugin_manager

# Auto-discover plugins on package import
plugin_manager.discover_and_load()
