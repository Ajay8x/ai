# AJAX AI ⚡
## Adaptive Intelligence & Autonomous eXecution
### Production-Grade Multilingual Voice & Chat AI Operating Layer

AJAX AI is a modular, high-performance personal AI assistant built in Python. It blends deep LLM reasoning, neural-network intent classification, PC automation, continuous learning, and multi-tier memory into a unified interface operating across **Chat, Voice, CLI, Local REST API, and Web UI**.

---

## ✨ Key Capabilities

1. **🧠 Multi-Provider AI Brain**: Seamless support for OpenAI, Groq, DeepSeek, OpenRouter, and local Ollama with zero-crash offline fallbacks.
2. **🎯 Neural Intent Engine**: 40+ default intents with Hindi, English, and Hinglish semantic understanding and confidence scoring.
3. **🎙️ Unified Voice Pipeline**: Wake word detection ("AJAX", "Jarvis"), VAD noise calibration, Google STT, and thread-safe interruptible TTS.
4. **💾 Multi-Tier Memory Engine**: Short-term session buffer, long-term SQLite persistent facts, episodic task logs, and built-in privacy filtering.
5. **🛡️ Safety & Guardrails**: Path traversal protection, strict shell command allowlisting, and user confirmation for destructive actions.
6. **💻 Safe PC Automation**: Hardware telemetry (CPU, RAM, GPU, Disk, Battery, Top Processes), App Launcher, Volume/Brightness, and Power management.
7. **📚 RAG Subsystem**: Parse, chunk, and index local documents (PDF, TXT, MD, Code) with cited retrieval.
8. **🌐 Web Intelligence**: DuckDuckGo search, Wikipedia knowledge extraction, YouTube playback, and quick-launch for 100+ recognized websites.
9. **🖥️ Modern Glassmorphic Web Dashboard**: Real-time live hardware graphs, chat streaming, and tool activity monitor.

---

## 🚀 Quick Start

### 1. Requirements Setup
```bash
pip install -r requirements.txt
```

### 2. Configuration (`.env`)
Copy `.env.example` to `.env` and set your desired LLM API key (optional — works offline by default!):
```bash
cp .env.example .env
```

### 3. Launching AJAX AI

- **Interactive CLI Mode** (Default with slash commands):
  ```bash
  python main.py
  ```

- **Web Dashboard & GUI Mode**:
  ```bash
  python main.py --gui
  ```

- **Voice Assistant Mode**:
  ```bash
  python main.py --voice
  ```

- **Local REST API Server**:
  ```bash
  python main.py --server --port 8000
  ```

- **System Diagnostics & Health Check**:
  ```bash
  python main.py --diagnostics
  ```

---

## 💬 CLI Slash Commands

| Command | Action |
| :--- | :--- |
| `/chat <query>` | Send a direct text message |
| `/voice` | Switch into voice assistant mode |
| `/tools` | List all 20+ registered tools and permissions |
| `/status` | View real-time CPU, RAM, Disk, and Battery diagnostics |
| `/diagnostics`| Run full self-health checks |
| `/memory` | Inspect saved long-term user facts |
| `/settings` | View active configuration |
| `/clear` | Start a new conversation session |
| `/help` | View help menu |
| `/exit` | Exit AJAX AI |

---

## 🧪 Testing & Evaluation

Run unit and integration test suite:
```bash
python tests/test_ajax.py
```

Run Intent Classification benchmark:
```bash
python training/evaluate.py
```

Retrain intent model on approved interaction samples:
```bash
python training/train.py
```

---

## 📂 Project Architecture

```text
Ai 3.0/
├── main.py                     # Unified multi-mode entry point
├── requirements.txt            # Dependency manifest
├── .env.example                # Configuration template
├── config/
│   ├── config_loader.py        # Typed configuration manager
│   └── sites.py                # Comprehensive web targets
├── core/
│   ├── logger.py               # Rotating structured log sinks
│   ├── safety.py               # Safety engine & path guardrails
│   ├── permissions.py          # SAFE, CONFIRM_REQUIRED, BLOCKED
│   ├── prompts.py              # Bilingual persona prompts
│   ├── context.py              # Context & memory assembly
│   ├── router.py               # Intent, tool & LLM router
│   ├── planner.py              # Multi-step ReAct agent planner
│   ├── diagnostics.py          # Self-healing diagnostics
│   ├── tts.py & stt.py         # Backward compatibility wrappers
├── ai/
│   ├── llm/                    # Base, OpenAI, Ollama & Factory fallback
│   ├── neural/                 # Semantic intent classifier
│   ├── rag/                    # Loader, chunker, vector store
│   └── vision/                 # Screen & OCR analyzer
├── tools/                      # Central Tool Registry & 20+ tools
├── voice/                      # TTS, STT, Wake word & Session manager
├── memory/                     # Multi-tier memory & privacy filter
├── system/                     # Telemetry monitor & background scheduler
├── database/                   # SQLite engine, models & CRUD
├── training/                   # Model trainer & benchmark evaluators
├── data/                       # Database, screenshots & intent datasets
├── tests/                      # Full test suite
└── logs/                       # Specialized rotating audit logs
```
