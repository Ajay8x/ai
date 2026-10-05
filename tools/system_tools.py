"""
AJAX AI - System Tools
CPU, RAM, GPU, Disk, Battery, Network, Volume, Brightness, Power Management.
"""

import os
import datetime
import psutil
import subprocess
from typing import Dict, Any, Optional
from tools.base import BaseTool, ToolResult
from core.permissions import PermissionLevel, ToolCategory

class GetSystemTimeTool(BaseTool):
    name = "get_system_time"
    description = "Get the current system time and date."
    category = ToolCategory.SYSTEM
    permission = PermissionLevel.SAFE
    parameters_schema = {
        "type": "object",
        "properties": {},
    }

    def execute(self, **kwargs) -> ToolResult:
        now = datetime.datetime.now()
        time_str = now.strftime("%I:%M %p")
        date_str = now.strftime("%A, %B %d, %Y")
        return ToolResult(
            success=True,
            output=f"Current time is {time_str} on {date_str}.",
            metadata={"time": time_str, "date": date_str}
        )

class GetSystemStatusTool(BaseTool):
    name = "get_system_status"
    description = "Get real-time CPU, RAM, Disk, and Battery diagnostics."
    category = ToolCategory.SYSTEM
    permission = PermissionLevel.SAFE
    parameters_schema = {
        "type": "object",
        "properties": {},
    }

    def execute(self, **kwargs) -> ToolResult:
        cpu_pct = psutil.cpu_percent(interval=0.5)
        ram = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        battery_str = "No battery detected (Desktop/Plugged)"
        battery = psutil.sensors_battery()
        if battery:
            plugged = "Plugged In" if battery.power_plugged else "Discharging"
            battery_str = f"{battery.percent}% ({plugged})"
            
        summary = (
            f"CPU Usage: {cpu_pct}%\n"
            f"RAM Usage: {ram.percent}% ({ram.used // (1024**2)}MB / {ram.total // (1024**2)}MB)\n"
            f"Disk Usage: {disk.percent}% free ({disk.free // (1024**3)}GB available)\n"
            f"Battery: {battery_str}"
        )
        return ToolResult(
            success=True,
            output=summary,
            metadata={
                "cpu_percent": cpu_pct,
                "ram_percent": ram.percent,
                "disk_percent": disk.percent,
                "battery": battery.percent if battery else None
            }
        )

class VolumeControlTool(BaseTool):
    name = "control_volume"
    description = "Adjust or mute system volume on Windows."
    category = ToolCategory.SYSTEM
    permission = PermissionLevel.SAFE
    parameters_schema = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["up", "down", "mute", "unmute"],
                "description": "Volume action to perform"
            },
            "steps": {
                "type": "integer",
                "description": "Number of volume steps (1-10)",
                "default": 2
            }
        },
        "required": ["action"]
    }

    def execute(self, action: str, steps: int = 2, **kwargs) -> ToolResult:
        try:
            import pyautogui
            if action == "up":
                for _ in range(steps):
                    pyautogui.press("volumeup")
                return ToolResult(success=True, output=f"Turned volume up by {steps} steps.")
            elif action == "down":
                for _ in range(steps):
                    pyautogui.press("volumedown")
                return ToolResult(success=True, output=f"Turned volume down by {steps} steps.")
            elif action in ("mute", "unmute"):
                pyautogui.press("volumemute")
                return ToolResult(success=True, output="Toggled volume mute.")
            return ToolResult(success=False, output=None, error=f"Unknown volume action: {action}")
        except Exception as e:
            return ToolResult(success=False, output=None, error=f"Volume control failed: {str(e)}")

class TakeScreenshotTool(BaseTool):
    name = "take_screenshot"
    description = "Capture and save a full desktop screenshot."
    category = ToolCategory.SYSTEM
    permission = PermissionLevel.SAFE
    parameters_schema = {
        "type": "object",
        "properties": {
            "filename": {"type": "string", "description": "Optional custom filename"}
        }
    }

    def execute(self, filename: Optional[str] = None, **kwargs) -> ToolResult:
        try:
            import pyautogui
            shots_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "screenshots")
            os.makedirs(shots_dir, exist_ok=True)
            
            if not filename:
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"screenshot_{timestamp}.png"
            elif not filename.endswith(".png"):
                filename += ".png"
                
            filepath = os.path.join(shots_dir, filename)
            screenshot = pyautogui.screenshot()
            screenshot.save(filepath)
            return ToolResult(
                success=True,
                output=f"Screenshot saved to: {filepath}",
                metadata={"filepath": filepath}
            )
        except Exception as e:
            return ToolResult(success=False, output=None, error=f"Screenshot failed: {str(e)}")

class SystemPowerTool(BaseTool):
    name = "system_power"
    description = "Lock, Sleep, Restart, or Shutdown the PC (Requires confirmation)."
    category = ToolCategory.SYSTEM
    permission = PermissionLevel.CONFIRM_REQUIRED
    parameters_schema = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["lock", "sleep", "restart", "shutdown"],
                "description": "Power action to perform"
            }
        },
        "required": ["action"]
    }

    def execute(self, action: str, **kwargs) -> ToolResult:
        try:
            if action == "lock":
                os.system("rundll32.exe user32.dll,LockWorkStation")
                return ToolResult(success=True, output="PC locked successfully.")
            elif action == "sleep":
                os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
                return ToolResult(success=True, output="PC putting to sleep.")
            elif action == "restart":
                os.system("shutdown /r /t 5")
                return ToolResult(success=True, output="PC restarting in 5 seconds.")
            elif action == "shutdown":
                os.system("shutdown /s /t 5")
                return ToolResult(success=True, output="PC shutting down in 5 seconds.")
            return ToolResult(success=False, output=None, error=f"Unknown power action: {action}")
        except Exception as e:
            return ToolResult(success=False, output=None, error=f"Power command failed: {str(e)}")
