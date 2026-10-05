"""
AJAX AI - Vision and Screen Intelligence
Extracts visual information from screenshots and desktop UI.
"""

import os
import datetime
from typing import Dict, Any, Optional
from core.logger import ajax_logger

class ScreenVisionEngine:
    def capture_and_inspect(self) -> Dict[str, Any]:
        """Capture active screen and return metadata."""
        try:
            import pyautogui
            shots_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "screenshots")
            os.makedirs(shots_dir, exist_ok=True)
            
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = os.path.join(shots_dir, f"vision_inspect_{timestamp}.png")
            
            screenshot = pyautogui.screenshot()
            screenshot.save(filepath)
            
            width, height = screenshot.size
            return {
                "success": True,
                "file_path": filepath,
                "resolution": f"{width}x{height}",
                "description": f"Captured screen at {width}x{height} resolution."
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

screen_vision = ScreenVisionEngine()
