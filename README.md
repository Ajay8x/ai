# Jarvis AI (2.0) 🤖

Jarvis is a modular, voice-controlled personal assistant built in Python. It can listen to your voice commands, control your computer, perform web searches, open websites and applications, manage media, and more.

## ✨ Features

*   **🎙️ Voice Interaction**: Listens to commands via the microphone and speaks back using `pyttsx3`.
*   **🌐 Web Searches**: Searches Wikipedia and Google for answers.
*   **▶️ YouTube Playback**: Plays requested songs/videos directly on YouTube.
*   **💻 System Controls**:
    *   **Power**: Shutdown, Restart, and Sleep PC.
    *   **Volume**: Increase, Decrease, or Mute system volume.
    *   **Media**: Play or Pause background media.
*   **📸 Screenshots**: Take screenshots of your screen instantly.
*   **📂 App Management**: Open and forcefully close Windows applications and websites.
*   **🧠 Memory**: Remember notes and recall them later.
*   **🌤️ Live Data**: Fetch live weather updates (via OpenWeatherMap) and top news headlines.

---

## 🛠️ Project Structure

The project has been refactored into a modular structure to keep the code clean and maintainable:

*   `main.py`: The entry point. It contains the main routing loop for voice commands.
*   `tts.py`: Handles Text-to-Speech (`pyttsx3`) setup and the `speak()` function.
*   `stt.py`: Handles Speech-to-Text (`SpeechRecognition`) setup and the `take_command()` function.
*   `system_ops.py`: Handles PC operations (Volume, Power, Screenshots, Opening/Closing apps).
*   `web_ops.py`: Handles Web operations (Search, YouTube, News).
*   `memory_ops.py`: Handles saving and reading notes from `memory.txt`.
*   `weather.py`: Handles fetching weather using the OpenWeatherMap API.
*   `app_cmd.py`: Contains a dictionary mapping spoken names to executable commands (e.g., "settings" -> "ms-settings:").
*   `close_cmd.py`: Contains a dictionary mapping spoken names to process names for forced closing.
*   `sites.py`: Contains a list of common website names and their URLs.

---

## 🚀 Installation & Setup

1. **Clone or Download** the repository to your local machine.
2. **Install Requirements**: Ensure you have Python installed, then run the following command to install all necessary libraries:
   ```bash
   pip install -r requirements.txt
   ```
3. **Run the Assistant**:
   ```bash
   python main.py
   ```

### 📋 Prerequisites (Libraries Used)
- `pyttsx3`
- `SpeechRecognition`
- `wikipedia`
- `pywhatkit`
- `PyAudio` (required for microphone input)
- `pyautogui` (required for media/volume control and screenshots)
- `requests` (required for API calls)

---

## 🗣️ Example Commands

*   *"Jarvis, what is Python?"* (Searches Wikipedia)
*   *"Jarvis, play Arijit Singh on YouTube"*
*   *"Jarvis, open Chrome"* / *"Jarvis, close Chrome"*
*   *"Jarvis, what's the weather in Mumbai?"*
*   *"Jarvis, take a screenshot"*
*   *"Jarvis, volume up"* / *"Jarvis, mute"*
*   *"Jarvis, remember that I have a meeting at 5 PM"*
*   *"Jarvis, what do you remember?"*
*   *"Jarvis, shutdown my computer"*

---
*Created as a modular AI assistant project.*
