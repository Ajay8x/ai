"""
AJAX AI - Wake Word Detector
Detects wake words ("AJAX", "Jarvis") from audio streams or queries.
"""

from config.config_loader import config
from core.logger import voice_logger
import re

class WakeWordDetector:
    def __init__(self):
        self.wake_words = ["ajax", "jarvis", "hey ajax", "hey jarvis", "ok ajax"]

    def contains_wake_word(self, text: str) -> bool:
        if not config.voice.wake_word_enabled:
            return True

        text_normalized = re.sub(r"\s+", " ", text.casefold()).strip()
        configured_wake = re.sub(r"\s+", " ", config.voice.wake_word.casefold()).strip()
        candidates = [configured_wake] if configured_wake else []
        candidates.extend(self.wake_words)

        for wake_word in sorted(set(candidates), key=len, reverse=True):
            pattern = rf"(?<!\w){re.escape(wake_word)}(?!\w)"
            if re.search(pattern, text_normalized):
                return True
        return False

    def strip_wake_word(self, text: str) -> str:
        """Removes the wake word prefix from the query string."""
        normalized = text.strip()
        candidates = [config.voice.wake_word.strip()] if config.voice.wake_word.strip() else []
        candidates.extend(self.wake_words)
        for wake_word in sorted(set(candidates), key=len, reverse=True):
            pattern = rf"^{re.escape(wake_word)}(?=\s|[,!:;]|$)"
            match = re.match(pattern, normalized, flags=re.IGNORECASE)
            if match:
                return normalized[match.end():].strip(" ,!:;").strip()
        return text.strip()

wake_word_detector = WakeWordDetector()
