"""
AJAX AI - Wake Word Detector
Detects wake words ("AJAX", "Jarvis") from audio streams or queries.
"""

from config.config_loader import config
from core.logger import voice_logger

class WakeWordDetector:
    def __init__(self):
        self.wake_words = ["ajax", "jarvis", "hey ajax", "hey jarvis", "ok ajax"]

    def contains_wake_word(self, text: str) -> bool:
        if not config.voice.wake_word_enabled:
            return True
            
        text_lower = text.lower()
        configured_wake = config.voice.wake_word.lower()
        
        if configured_wake in text_lower:
            return True
            
        for w in self.wake_words:
            if w in text_lower:
                return True
        return False

    def strip_wake_word(self, text: str) -> str:
        """Removes the wake word prefix from the query string."""
        text_lower = text.lower()
        for w in self.wake_words:
            if text_lower.startswith(w):
                return text[len(w):].strip(", ").strip()
        return text.strip()

wake_word_detector = WakeWordDetector()
