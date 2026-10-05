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

class SetAlarmTool(BaseTool):
    name = "set_alarm"
    description = "Set an alarm for a specific time (HH:MM) today."
    category = ToolCategory.SCHEDULER
    permission = PermissionLevel.SAFE
    parameters_schema = {
        "type": "object",
        "properties": {
            "time_str": {"type": "string", "description": "Time in 24-hour HH:MM format (e.g. 07:30, 18:00)"},
            "label": {"type": "string", "description": "Alarm label or reason", "default": "Alarm!"}
        },
        "required": ["time_str"]
    }

    def execute(self, time_str: str, label: str = "Alarm!", **kwargs) -> ToolResult:
        try:
            target_time = datetime.datetime.strptime(time_str, "%H:%M").time()
            now = datetime.datetime.now()
            target_dt = datetime.datetime.combine(now.date(), target_time)
            
            if target_dt <= now:
                target_dt += datetime.timedelta(days=1)
                
            delay_seconds = (target_dt - now).total_seconds()

            def alarm_worker():
                time.sleep(delay_seconds)
                ajax_logger.info(f"ALARM ALERT: {label}")
                try:
                    import winsound
                    for _ in range(3):
                        winsound.Beep(1500, 500)
                        time.sleep(0.2)
                except Exception:
                    pass
                try:
                    from voice.tts import tts_engine
                    tts_engine.speak(f"Alarm ringing: {label}")
                except Exception:
                    pass

            thread = threading.Thread(target=alarm_worker, daemon=True)
            thread.start()

            return ToolResult(
                success=True,
                output=f"Alarm scheduled for {target_dt.strftime('%I:%M %p')} ({label})."
            )
        except Exception as e:
            return ToolResult(success=False, output=None, error=f"Failed to parse alarm time: {str(e)}")
