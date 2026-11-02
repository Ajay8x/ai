"""
AJAX AI - Speech-to-Text Engine
Captures microphone audio and converts to text via Google Speech Recognition or local fallback.
"""

import os
from typing import Optional

try:
    import speech_recognition as sr
    SPEECH_RECOGNITION_AVAILABLE = True
except ImportError:
    sr = None
    SPEECH_RECOGNITION_AVAILABLE = False
from config.config_loader import config
from core.logger import voice_logger, error_logger

QUERY_LOG_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "query.txt")

class STTEngine:
    def __init__(self):
        self.recognizer: Optional[object] = sr.Recognizer() if sr else None
        if self.recognizer:
            self.recognizer.pause_threshold = 0.8
            self.recognizer.dynamic_energy_threshold = True

    @property
    def available(self) -> bool:
        return bool(SPEECH_RECOGNITION_AVAILABLE and self.recognizer)

    def listen_command(self) -> str:
        """Listens from microphone and returns transcribed lowercase text."""
        if not self.available:
            error_logger.warning("SpeechRecognition is not installed; voice input is unavailable.")
            return "none"

        try:
            with sr.Microphone() as source:
                voice_logger.info("Microphone listening...")
                # Calibrate for ambient noise
                self.recognizer.adjust_for_ambient_noise(source, duration=0.3)
                audio = self.recognizer.listen(source, timeout=8, phrase_time_limit=10)

            voice_logger.info("Transcribing audio...")
            languages = [config.voice.stt_language]
            languages.extend(
                language.strip()
                for language in config.voice.stt_fallback_languages.split(",")
                if language.strip()
            )
            query = None
            for language in dict.fromkeys(languages):
                try:
                    query = self.recognizer.recognize_google(audio, language=language)
                    if query:
                        break
                except sr.UnknownValueError:
                    continue
                except sr.RequestError as e:
                    error_logger.warning(f"Speech recognition service error: {e}")
                    break
            if not query:
                return "none"
            voice_logger.info(f"Recognized Speech: '{query}'")
        except Exception as e:
            if sr and isinstance(e, (sr.WaitTimeoutError, sr.UnknownValueError)):
                return "none"
            error_logger.warning(f"STT recognition error: {e}")
            return "none"

        query_clean = query.lower().strip()

        # Log query to MongoDB Atlas
        try:
            from database.db import is_mongo_active, get_mongo_db
            if is_mongo_active():
                db = get_mongo_db()
                db.voice_queries.insert_one({"query": query_clean})
        except Exception:
            pass

        return query_clean

stt_engine = STTEngine()

def take_command() -> str:
    return stt_engine.listen_command()
