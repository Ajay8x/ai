"""
AJAX AI - Safety and Validation Engine
Protects system files, prevents dangerous shell injections, and enforces user confirmation policies.
"""

import os
import re
from typing import Tuple, Optional
from core.permissions import PermissionLevel
from core.logger import security_logger

# Critical directories that must NEVER be modified or deleted
PROTECTED_SYSTEM_PATHS = [
    r"C:\Windows",
    r"C:\Program Files\Windows",
    r"C:\Boot",
    r"C:\Recovery",
]

# Prohibited shell commands / patterns
DANGEROUS_PATTERNS = [
    r"format\s+[a-zA-Z]:",
    r"rmdir\s+/s\s+/q\s+C:\\",
    r"del\s+/f\s+/s\s+/q\s+C:\\Windows",
    r"reg\s+delete",
    r"bcdedit",
    r"powershell\s+-[eE]", # encoded commands
    r"cipher\s+/w",
]

class SafetyEngine:
    @staticmethod
    def is_path_safe(path: str, for_writing: bool = False) -> Tuple[bool, str]:
        """Validates whether a filesystem path is safe to access/modify."""
        if not path:
            return False, "Path is empty."
        
        abs_path = os.path.abspath(path)
        
        # Check against protected system paths
        for protected in PROTECTED_SYSTEM_PATHS:
            if abs_path.lower().startswith(protected.lower()):
                security_logger.warning(f"BLOCKED: Attempt to access protected path: {abs_path}")
                return False, f"Access to system protected directory '{protected}' is strictly blocked."
                
        # Additional checks for root drive deletion
        if for_writing and abs_path.lower() in [r"c:\\", r"c:", r"d:\\", r"d:"]:
            return False, "Modifying root directory directly is prohibited."
            
        return True, "Path is safe."

    @staticmethod
    def validate_command_safety(command_str: str) -> Tuple[bool, str]:
        """Scans command strings for malicious injection patterns."""
        for pattern in DANGEROUS_PATTERNS:
            if re.search(pattern, command_str, re.IGNORECASE):
                security_logger.warning(f"BLOCKED: Dangerous command pattern detected: {command_str}")
                return False, f"Command matches dangerous pattern: '{pattern}'"
        return True, "Command is safe."

    @staticmethod
    def check_tool_permission(permission: PermissionLevel, requires_user_ack: bool = True) -> Tuple[bool, str]:
        """Enforces execution policy for a given tool permission."""
        if permission == PermissionLevel.BLOCKED:
            security_logger.warning("Execution BLOCKED by permission policy.")
            return False, "Action is blocked by safety policy."
            
        if permission == PermissionLevel.CONFIRM_REQUIRED and requires_user_ack:
            return True, "CONFIRM_REQUIRED"
            
        return True, "APPROVED"

safety_engine = SafetyEngine()
