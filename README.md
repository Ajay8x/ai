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
*   `core/`: Contains core intelligence (`tts.py`, `stt.py`, `memory_ops.py`).
*   `commands/`: Contains specific action handlers (`system_ops.py`, `web_ops.py`, `timer_ops.py`, `app_cmd.py`, `close_cmd.py`).
*   `services/`: Contains external API integrations (`weather.py`).
*   `config/`: Contains configuration files (`sites.py`).
*   `data/`: Contains persistent data like `query.txt` and `memory.txt`.

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
- `psutil` (required for battery and CPU monitoring)

---

## 🗣️ Example Commands

*   *"Jarvis, what is Python?"* (Searches Wikipedia)
*   *"Jarvis, play Arijit Singh on YouTube"*
*   *"Jarvis, open Chrome"* / *"Jarvis, close Chrome"*
*   *"Jarvis, what's the weather in Mumbai?"*
*   *"Jarvis, take a screenshot"*
*   *"Jarvis, volume up"* / *"Jarvis, mute"*
*   *"Jarvis, check battery"* / *"Jarvis, check CPU"*
*   *"Jarvis, set a timer for 10 minutes"*
*   *"Jarvis, set an alarm for 7 AM"*
*   *"Jarvis, remember that I have a meeting at 5 PM"*
*   *"Jarvis, what do you remember?"*
*   *"Jarvis, shutdown my computer"*

---
*Created as a modular AI assistant project.*
