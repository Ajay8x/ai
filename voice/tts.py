"""
AJAX AI - Text-to-Speech Engine
Thread-safe pyttsx3 synthesizer with volume/rate controls and voice profiles.
"""

import threading
import datetime
from typing import Optional
from config.config_loader import config
from core.logger import voice_logger, error_logger

class TTSEngine:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TTSEngine, cls).__new__(cls)
            cls._instance.initialized = False
        return cls._instance

    def __init__(self):
        if self.initialized:
            return
        self.engine = None
        self._init_engine()
        self.initialized = True

    def _init_engine(self):
        try:
            import pyttsx3
            self.engine = pyttsx3.init()
            self.engine.setProperty('rate', config.voice.rate or 170)
            self.engine.setProperty('volume', config.voice.volume or 1.0)
            voice_logger.info("pyttsx3 TTS Engine initialized successfully.")
        except Exception as e:
            error_logger.warning(f"Failed to initialize pyttsx3 TTS engine: {e}")
            self.engine = None

    def speak(self, text: str):
        """Speak the provided text aloud in a thread-safe manner."""
        if not text or not config.voice.enabled:
            return
            
        voice_logger.info(f"Speaking: '{text}'")
        with self._lock:
            if not self.engine:
                self._init_engine()
                
            if self.engine:
                try:
                    self.engine.say(text)
                    self.engine.runAndWait()
                except Exception as e:
                    error_logger.error(f"TTS Speech error: {e}")
                    # Re-init on COM/Audio failure
                    self._init_engine()

    def wish_user(self):
        """Greets the user according to the time of the day."""
        hour = datetime.datetime.now().hour
        if 0 <= hour < 12:
            greeting = "Good Morning!"
        elif 12 <= hour < 18:
            greeting = "Good Afternoon!"
        else:
            greeting = "Good Evening!"

        intro = f"{greeting} I am AJAX, your Adaptive AI Assistant. How can I help you today?"
        self.speak(intro)

tts_engine = TTSEngine()

def speak(text: str):
    tts_engine.speak(text)

def wish_user():
    tts_engine.wish_user()
