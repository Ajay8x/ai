"""
AJAX AI - Scheduler Tools
Non-blocking background timers, alarms, and reminders.
"""

import time
import threading
import datetime
from typing import Dict, Any, Optional
from tools.base import BaseTool, ToolResult
from core.permissions import PermissionLevel, ToolCategory
from core.logger import ajax_logger

class SetTimerTool(BaseTool):
    name = "set_timer"
    description = "Set a non-blocking countdown timer in seconds or minutes with an alert."
    category = ToolCategory.SCHEDULER
    permission = PermissionLevel.SAFE
    parameters_schema = {
        "type": "object",
        "properties": {
            "seconds": {"type": "integer", "description": "Duration of timer in seconds", "default": 60},
            "message": {"type": "string", "description": "Alert message when timer expires", "default": "Timer finished!"}
        },
        "required": ["seconds"]
    }

    def execute(self, seconds: int = 60, message: str = "Timer finished!", **kwargs) -> ToolResult:
        def timer_worker():
            time.sleep(seconds)
            ajax_logger.info(f"TIMER ALERT: {message}")
            try:
                import winsound
                winsound.Beep(1000, 1000)
            except Exception:
                pass
            try:
                from voice.tts import tts_engine
                tts_engine.speak(f"Attention: {message}")
            except Exception:
                pass

        thread = threading.Thread(target=timer_worker, daemon=True)
        thread.start()
        
        mins, secs = divmod(seconds, 60)
        time_desc = f"{mins} minute(s) " if mins else ""
        time_desc += f"{secs} second(s)" if secs else ""
        return ToolResult(
            success=True,
            output=f"Timer set for {time_desc}. I will alert you when it expires."
        )


