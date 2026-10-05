"""
AJAX AI - Application Management Tools
Handles opening, closing, and finding applications installed on Windows.
"""

import os
import subprocess
import psutil
from typing import Dict, Any, Optional
from tools.base import BaseTool, ToolResult
from core.permissions import PermissionLevel, ToolCategory

# Common Windows App Launch Targets
COMMON_APPS = {
    "notepad": "notepad.exe",
    "calc": "calc.exe",
    "calculator": "calc.exe",
    "chrome": "chrome",
    "google chrome": "chrome",
    "edge": "msedge",
    "ms edge": "msedge",
    "cmd": "cmd.exe",
    "command prompt": "cmd.exe",
    "terminal": "wt.exe",
    "powershell": "powershell.exe",
    "explorer": "explorer.exe",
    "file explorer": "explorer.exe",
    "settings": "start ms-settings:",
    "paint": "mspaint.exe",
    "task manager": "taskmgr.exe",
    "word": "winword",
    "excel": "excel",
    "powerpoint": "powerpnt",
    "code": "code",
    "vscode": "code"
}

class OpenApplicationTool(BaseTool):
    name = "open_application"
    description = "Launch an installed software or desktop application on Windows."
    category = ToolCategory.APPLICATION
    permission = PermissionLevel.SAFE
    parameters_schema = {
        "type": "object",
        "properties": {
            "app_name": {
                "type": "string",
                "description": "Name of application to launch (e.g. chrome, notepad, calculator, vscode)"
            }
        },
        "required": ["app_name"]
    }

    def execute(self, app_name: str, **kwargs) -> ToolResult:
        app_clean = app_name.lower().strip()
        target = COMMON_APPS.get(app_clean, app_clean)
        
        try:
            if target.startswith("start "):
                os.system(target)
            else:
                # Use os.startfile or subprocess for clean launching without hanging
                try:
                    os.startfile(target)
                except Exception:
                    subprocess.Popen(target, shell=True)
                    
            return ToolResult(success=True, output=f"Launched {app_name} successfully.")
        except Exception as e:
            # Fallback to direct shell execution of the query
            try:
                os.system(f"start {app_name}")
                return ToolResult(success=True, output=f"Launched {app_name}.")
            except Exception as ex:
                return ToolResult(success=False, output=None, error=f"Could not open application '{app_name}': {str(e)}")

class CloseApplicationTool(BaseTool):
    name = "close_application"
    description = "Close or terminate a running application on Windows."
    category = ToolCategory.APPLICATION
    permission = PermissionLevel.SAFE
    parameters_schema = {
        "type": "object",
        "properties": {
            "app_name": {
                "type": "string",
                "description": "Name of application to close (e.g. chrome, notepad, calc)"
            }
        },
        "required": ["app_name"]
    }

    def execute(self, app_name: str, **kwargs) -> ToolResult:
        app_clean = app_name.lower().strip().replace(".exe", "")
        killed = False
        
        for proc in psutil.process_iter(['name', 'pid']):
            try:
                proc_name = proc.info['name'].lower().replace(".exe", "")
                if app_clean in proc_name or proc_name in app_clean:
                    proc.terminate()
                    killed = True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
                
        if killed:
            return ToolResult(success=True, output=f"Closed application: {app_name}")
        else:
            return ToolResult(success=False, output=None, error=f"No running process found for '{app_name}'.")
