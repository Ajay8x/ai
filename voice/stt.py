"""
AJAX AI - Speech-to-Text Engine
Captures microphone audio and converts to text via Google Speech Recognition or local fallback.
"""

import os
import speech_recognition as sr
from config.config_loader import config
from core.logger import voice_logger, error_logger

QUERY_LOG_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "query.txt")

class STTEngine:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.recognizer.pause_threshold = 0.8
        self.recognizer.dynamic_energy_threshold = True

    def listen_command(self) -> str:
        """Listens from microphone and returns transcribed lowercase text."""
        try:
            with sr.Microphone() as source:
                voice_logger.info("Microphone listening...")
                # Calibrate for ambient noise
                self.recognizer.adjust_for_ambient_noise(source, duration=0.3)
                audio = self.recognizer.listen(source, timeout=8, phrase_time_limit=10)

            voice_logger.info("Transcribing audio...")
            query = self.recognizer.recognize_google(audio, language="en-IN")
            voice_logger.info(f"Recognized Speech: '{query}'")
        except sr.WaitTimeoutError:
            return "none"
        except sr.UnknownValueError:
            return "none"
        except Exception as e:
            error_logger.warning(f"STT recognition error: {e}")
            return "none"

        query_clean = query.lower().strip()

        # Log query to data/query.txt (Preserving legacy behavior)
        try:
            with open(QUERY_LOG_FILE, "a", encoding="utf-8") as f:
                f.write(query_clean + "\n")
        except Exception:
            pass

        return query_clean

stt_engine = STTEngine()

def take_command() -> str:
    return stt_engine.listen_command()
