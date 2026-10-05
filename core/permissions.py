"""
AJAX AI - Permissions and Safety Definitions
"""

from enum import Enum

class PermissionLevel(str, Enum):
    SAFE = "SAFE"                       # Automatically executable for safe operations (read, info)
    CONFIRM_REQUIRED = "CONFIRM_REQUIRED" # Consequential actions (file delete, power, settings)
    BLOCKED = "BLOCKED"                 # Never allowed (malware, credential theft, raw shell)

class ToolCategory(str, Enum):
    SYSTEM = "SYSTEM"
    FILESYSTEM = "FILESYSTEM"
    APPLICATION = "APPLICATION"
    WEB = "WEB"
    MEDIA = "MEDIA"
    SCHEDULER = "SCHEDULER"
    MEMORY = "MEMORY"
    CUSTOM = "CUSTOM"
