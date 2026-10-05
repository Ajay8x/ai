"""
AJAX AI - Voice Session Coordinator
Orchestrates continuous speech listening, wake word filtering, and verbal responses.
"""

from voice.stt import stt_engine
from voice.tts import tts_engine
from voice.wake_word import wake_word_detector
from core.router import router
from database.crud import create_conversation
from core.logger import voice_logger

class VoiceSessionManager:
    def __init__(self):
        self.is_running = False
        self.conversation_id = create_conversation("Voice Session")

    def run_loop(self):
        self.is_running = True
        tts_engine.wish_user()

        while self.is_running:
            query = stt_engine.listen_command()
            if query == "none" or not query:
                continue

            # Check for wake word if configured
            if not wake_word_detector.contains_wake_word(query):
                continue

            cleaned_query = wake_word_detector.strip_wake_word(query)
            if not cleaned_query:
                tts_engine.speak("Yes, I am listening.")
                continue

            # Exit command
            if cleaned_query in ["exit", "stop", "goodbye", "quit", "band ho jao"]:
                tts_engine.speak("Goodbye! Have a great day.")
                self.is_running = False
                break

            # Route query through central AI engine
            result = router.process_query(
                query=cleaned_query,
                conversation_id=self.conversation_id,
                modality="voice"
            )

            # Speak AI response
            response_text = result.get("response", "")
            if response_text:
                tts_engine.speak(response_text)

voice_manager = VoiceSessionManager()
