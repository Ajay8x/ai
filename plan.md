# AJAX AI
## Adaptive Intelligence & Autonomous eXecution
### Ultimate Production-Grade AI Assistant — Complete Master Development Specification

You are a senior AI architect, LLM engineer, ML engineer, Python developer, voice-AI engineer, computer-vision engineer, cybersecurity engineer, Windows automation engineer, software architect, DevOps engineer, database engineer, and UI/UX engineer.

I have an existing Python-based AI assistant called **AJAX AI**.

Your job is to transform it into a highly advanced, modular, production-quality personal AI assistant.

IMPORTANT:

**Do not remove existing functionality.**

**Do not blindly rewrite the project.**

First inspect the entire existing project, understand how it works, identify existing features, dependencies, entry points, APIs, UI, voice system, command system, databases and configuration, then integrate the new architecture.

The final AJAX AI must be modular, extensible, secure, fast, maintainable and capable of operating through both **CHAT and VOICE**.

---

# 1. AJAX AI IDENTITY

Name:

AJAX AI

Full form:

**Adaptive Intelligence & Autonomous eXecution**

AJAX is a personal AI assistant designed to interact naturally with the user and safely control the user's computer.

AJAX should support:

- Conversation
- Reasoning
- Natural-language understanding
- Voice conversation
- Memory
- Learning
- PC control
- Application control
- File management
- Browser automation
- Web access
- APIs
- RAG
- Vision
- Tool calling
- Function calling
- Custom commands
- Plugins
- Neural-network intent detection
- LLM reasoning
- Offline fallback
- Security
- User confirmation
- System monitoring
- Diagnostics

---

# 2. CORE PRINCIPLE

AJAX must not be a simple chatbot.

It must be a complete AI-agent system.

Architecture:

```text
                    AJAX AI
                       │
          ┌────────────┴────────────┐
          │                         │
       CHAT                      VOICE
          │                         │
          └────────────┬────────────┘
                       ↓
                INPUT PROCESSOR
                       ↓
              CONTEXT MANAGER
                       ↓
              MEMORY RETRIEVAL
                       ↓
                 AI BRAIN
          ┌────────────┼────────────┐
          ↓            ↓            ↓
        LLM       Neural Network   RAG
          │            │            │
          └────────────┼────────────┘
                       ↓
                 AGENT PLANNER
                       ↓
                  TOOL ROUTER
                       ↓
     ┌────────┬────────┬────────┬────────┐
     ↓        ↓        ↓        ↓        ↓
    PC      FILES     WEB     APPS     APIs
     │        │        │        │        │
     └────────┴────────┴────────┴────────┘
                       ↓
                 SAFETY ENGINE
                       ↓
                ACTION EXECUTION
                       ↓
                 RESULT VALIDATION
                       ↓
                RESPONSE GENERATOR
                       ↓
              CHAT + VOICE OUTPUT
```

---

# 3. AI BRAIN

Use a modern pretrained LLM/Transformer as the primary conversational intelligence.

Do NOT attempt to train a ChatGPT-scale model from scratch.

Create an abstraction layer:

```python
class LLMProvider:
    async def generate(self, messages, tools=None):
        ...
```

Support provider adapters.

Possible providers:

- OpenAI-compatible APIs
- Local LLM
- Ollama
- Hugging Face
- Other compatible providers

The rest of AJAX must not depend directly on one provider.

Allow model switching from configuration.

---

# 4. LLM CAPABILITIES

The LLM layer should support:

- Natural conversation
- Context understanding
- Multi-turn conversation
- Reasoning
- Summarization
- Classification
- Structured output
- JSON output
- Tool calling
- Function calling
- Streaming
- System instructions
- Conversation summarization
- Context compression
- Multilingual conversation
- Hindi
- English
- Hinglish

Never expose private chain-of-thought.

Only expose concise reasoning summaries when appropriate.

---

# 5. NEURAL NETWORK ENGINE

Implement a dedicated Neural Network/ML subsystem.

It must handle:

- Intent classification
- Command classification
- Semantic similarity
- Entity detection
- Confidence scoring
- Command routing
- Custom intent learning

Recommended technologies:

- PyTorch
- Transformers
- sentence-transformers
- scikit-learn

Use pretrained embeddings where appropriate.

Do not unnecessarily train massive models from scratch.

---

# 6. INTENT ENGINE

Initial intents:

```text
GREETING
GENERAL_CHAT
OPEN_APPLICATION
CLOSE_APPLICATION
RESTART_APPLICATION
APPLICATION_STATUS
SYSTEM_INFO
CPU_STATUS
RAM_STATUS
GPU_STATUS
BATTERY_STATUS
DISK_STATUS
NETWORK_STATUS
BLUETOOTH_STATUS
WIFI_STATUS
OPEN_FOLDER
SEARCH_FILE
READ_FILE
CREATE_FILE
EDIT_FILE
DELETE_FILE
RENAME_FILE
COPY_FILE
MOVE_FILE
OPEN_WEBSITE
SEARCH_WEB
TIME
DATE
WEATHER
SCREENSHOT
SCREEN_RECORD
VOLUME_CONTROL
BRIGHTNESS_CONTROL
LOCK_PC
SLEEP_PC
RESTART_PC
SHUTDOWN_PC
MEMORY_SAVE
MEMORY_DELETE
MEMORY_SEARCH
SYSTEM_DIAGNOSTICS
HELP
SETTINGS
```

Allow unlimited custom intents.

---

# 7. CONFIDENCE SYSTEM

Every prediction must return:

```json
{
  "intent": "OPEN_APPLICATION",
  "confidence": 0.98,
  "entities": {
    "application": "chrome"
  }
}
```

Confidence levels:

```text
HIGH
MEDIUM
LOW
```

Rules:

HIGH:
→ continue automatically for safe operations.

MEDIUM:
→ use LLM verification or ask clarification.

LOW:
→ use LLM/fallback.

Never perform destructive actions based solely on low confidence.

---

# 8. NATURAL LANGUAGE

Support variations:

```text
Open Chrome
Can you open Chrome?
Please launch Chrome
Chrome खोल दो
Chrome start कर दो
भाई chrome खोल
Google Chrome चला दो
```

All should map to the same semantic intent.

Support:

- English
- Hindi
- Hinglish

Automatically detect language where practical.

---

# 9. CHAT SYSTEM

Create a premium modern chat interface.

Features:

- New chat
- Conversation history
- Search chats
- Rename chats
- Delete chats
- Archive chats
- Pin chats
- Export chats
- Import chats
- Markdown
- Code blocks
- Syntax highlighting
- Copy response
- Regenerate
- Edit user message
- Retry
- Stop generation
- Streaming
- Typing indicator
- Tool status
- File attachments
- Image attachments
- Voice button
- Drag-and-drop
- Keyboard shortcuts

---

# 10. VOICE AI

Implement complete voice pipeline:

```text
Microphone
↓
Noise Reduction
↓
Voice Activity Detection
↓
Wake Word
↓
Speech-to-Text
↓
AJAX AI
↓
LLM / Tool Engine
↓
Text-to-Speech
↓
Speaker
```

Features:

- Wake word
- Push-to-talk
- Continuous listening
- Voice activity detection
- Speech recognition
- Noise reduction
- Silence detection
- Text-to-speech
- Interruptible TTS
- Voice selection
- Speech speed
- Voice volume
- Microphone selection
- Speaker selection
- Voice history
- Voice error recovery

Chat and voice MUST use the same AI processing pipeline.

---

# 11. WAKE WORD

Support configurable wake word:

```text
AJAX
```

Example:

"AJAX, open Chrome."

Allow custom wake words.

Wake-word detection must not permanently consume excessive resources.

---

# 12. MEMORY

Implement:

## Short-term memory

Current conversation context.

## Long-term memory

Useful user-approved information.

## Episodic memory

Important previous interactions.

## Semantic memory

Embedded knowledge for retrieval.

Memory operations:

```text
SAVE
SEARCH
UPDATE
DELETE
SUMMARIZE
FORGET
```

Provide a memory-management UI.

The user must be able to inspect and delete stored memories.

Do not store sensitive information unless explicitly authorized.

---

# 13. RAG

Implement Retrieval-Augmented Generation.

Supported sources:

- PDF
- TXT
- Markdown
- DOCX
- Code
- Local folders
- User-provided documents

Pipeline:

```text
Document
↓
Chunking
↓
Embedding
↓
Vector Storage
↓
Retriever
↓
Relevant Context
↓
LLM
```

Provide source references when appropriate.

---

# 14. VISION

Add optional computer-vision capability.

AJAX should be able to analyze user-provided images.

Possible capabilities:

- Image understanding
- Screenshot analysis
- UI recognition
- OCR
- Text extraction
- Object recognition where supported
- Error screenshot analysis

Do not claim to see something if image processing failed.

---

# 15. SCREEN UNDERSTANDING

Optional computer-use layer.

AJAX may inspect screenshots to understand the UI.

Architecture:

```text
Screenshot
↓
Vision Model
↓
UI Understanding
↓
Action Planning
↓
Safety Check
↓
Mouse/Keyboard Action
```

Require confirmation for consequential actions.

---

# 16. TOOL SYSTEM

Create a centralized tool registry.

Every tool must define:

```text
Name
Description
Parameters
Validation
Permission
Execution
Result
Error handling
```

Example:

```python
Tool(
    name="open_application",
    description="Open an installed application",
    permission="SAFE"
)
```

---

# 17. PC CONTROL

Support safe Windows operations:

- Open applications
- Close applications
- Restart applications
- CPU information
- RAM information
- GPU information
- Disk information
- Battery
- Network
- Wi-Fi
- Bluetooth
- Processes
- Services
- Environment variables
- Windows version
- System uptime
- Temperature where available
- Folder opening
- File searching
- Screenshot
- Screen recording
- Clipboard
- Volume
- Brightness
- Lock
- Sleep
- Restart
- Shutdown

---

# 18. FILE SYSTEM

Implement controlled file operations:

- Search
- Read
- Create
- Rename
- Copy
- Move
- Delete
- List
- Metadata
- File size
- Duplicate detection

Protect system directories.

Require confirmation for deletion.

Never allow arbitrary unrestricted filesystem access.

---

# 19. APPLICATION CONTROL

Maintain application registry.

Example:

```json
{
  "chrome": "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
}
```

Allow:

- Launch
- Close
- Restart
- Detect running state

Automatically discover applications where practical.

---

# 20. BROWSER CONTROL

Provide optional browser tools.

Capabilities:

- Open website
- Search web
- Read webpage
- Navigate
- Fill forms
- Click approved controls
- Extract information

Require confirmation before:

- Purchases
- Account changes
- Sending messages
- Submitting forms
- Deleting online data

---

# 21. WEB SEARCH

AJAX should have a web-search abstraction.

Search pipeline:

```text
Question
↓
Search
↓
Retrieve sources
↓
Analyze
↓
Answer
↓
Cite sources
```

Never fabricate search results.

---

# 22. PLUGIN SYSTEM

Create a plugin architecture.

Example:

```text
plugins/
├── weather/
├── calculator/
├── browser/
├── music/
├── productivity/
└── custom/
```

Each plugin should have:

```text
manifest
name
version
permissions
tools
configuration
```

Plugins must run inside a permission-controlled environment.

---

# 23. SAFETY ENGINE

Every tool call must pass:

```text
User Request
↓
Intent
↓
Tool
↓
Permission
↓
Safety Validation
↓
Confirmation if needed
↓
Execution
```

Permission levels:

```text
SAFE
CONFIRM_REQUIRED
BLOCKED
```

SAFE examples:

- Check CPU
- Open calculator
- Get battery status

CONFIRM_REQUIRED:

- Delete file
- Restart PC
- Shutdown PC
- Modify important settings
- Install software
- Send external message

BLOCKED:

- Credential theft
- Malware
- Unauthorized access
- Destructive activity
- Harmful activity

---

# 24. SHELL SAFETY

NEVER allow the LLM unrestricted shell execution.

Do not do:

```python
os.system(llm_generated_command)
```

Instead create an allowlisted command/tool layer.

Validate:

- Command
- Arguments
- Paths
- Permissions
- Target

---

# 25. CONTINUOUS LEARNING

Implement controlled learning.

Store candidate training examples:

```json
{
  "text": "chrome खोल दो",
  "intent": "OPEN_APPLICATION",
  "confidence": 0.97,
  "source": "voice",
  "approved": false
}
```

Do NOT automatically train immediately.

Pipeline:

```text
Interaction
↓
Candidate Data
↓
Review
↓
Approval
↓
Dataset
↓
Training
↓
Validation
↓
Evaluation
↓
Model Version
↓
Deployment
```

---

# 26. TRAINING SYSTEM

Commands:

```bash
python train.py
python evaluate.py
python predict.py
```

Display:

- Epoch
- Loss
- Accuracy
- Validation loss
- Validation accuracy
- Precision
- Recall
- F1
- Dataset size
- Model version

---

# 27. MODEL VERSIONING

Never overwrite a production model blindly.

Use:

```text
models/
ajax_v1/
ajax_v2/
ajax_v3/
```

Store:

- Version
- Date
- Dataset
- Metrics
- Configuration

Support rollback.

---

# 28. MODEL HEALTH

At startup verify:

- Model exists
- Model loads
- Correct version
- Correct architecture
- Dependencies
- Configuration

If model fails:

```text
Load previous working model
```

If no model:

```text
Use LLM fallback
```

---

# 29. OFFLINE MODE

AJAX should degrade gracefully.

Priority:

```text
Cloud LLM
↓
Local LLM
↓
Local Neural Network
↓
Legacy AJAX
↓
Basic command system
```

Local PC commands should continue working even if internet is unavailable.

---

# 30. MULTIMODAL SYSTEM

Support:

- Text
- Voice
- Images
- Screenshots
- Documents

Design the system so additional modalities can be added later.

---

# 31. CONTEXT MANAGEMENT

Do not blindly send the entire conversation to the LLM.

Use:

```text
Recent messages
+
Conversation summary
+
Relevant memories
+
Relevant RAG documents
+
Current user request
```

Implement context-window management.

---

# 32. AGENT PLANNER

For complex tasks:

```text
User Request
↓
Task Understanding
↓
Plan
↓
Tool Selection
↓
Execute
↓
Observe Result
↓
Continue / Stop
↓
Final Response
```

The agent must have maximum step limits to prevent infinite loops.

---

# 33. TASK MANAGEMENT

AJAX should support multi-step tasks.

Example:

"Find all large files in Downloads, group them by extension and show me what can be deleted."

AJAX should:

1. Inspect Downloads
2. Find large files
3. Analyze
4. Group
5. Present results
6. Ask confirmation before deletion

---

# 34. SCHEDULER

Add optional task scheduling.

Support:

- One-time tasks
- Recurring tasks
- Reminders
- Scheduled PC operations

Require confirmation for dangerous scheduled actions.

---

# 35. SYSTEM MONITOR

Provide real-time monitoring:

- CPU
- RAM
- GPU
- Disk
- Network
- Battery
- Processes
- Temperature when available

Create dashboard graphs.

---

# 36. SELF-DIAGNOSTICS

AJAX should have:

```text
/status
/diagnostics
/health
```

Check:

- LLM
- Neural model
- Voice
- TTS
- Database
- Memory
- Tools
- Network
- Storage

Return clear status.

---

# 37. SECURITY

Implement:

- Secrets management
- `.env`
- Permission system
- Tool allowlist
- Path validation
- Input validation
- Audit logs
- Rate limits
- Confirmation system
- Secure subprocess handling
- Plugin permissions

Never log:

- API keys
- Passwords
- Access tokens
- Sensitive credentials

---

# 38. DATABASE

Use SQLite initially.

Store:

- Conversations
- Messages
- Memories
- Tool usage
- Settings
- Training examples
- Model versions
- Tasks

Design database layer so PostgreSQL can be added later.

---

# 39. BACKUP

Provide:

```text
backup/
restore/
```

Backup:

- Database
- Configuration
- Memory
- Intent dataset
- Model metadata

Do not expose secrets in backups.

---

# 40. IMPORT / EXPORT

Support:

- Conversation export
- Memory export
- Intent export
- Training dataset export
- Configuration export

Use JSON/CSV where appropriate.

---

# 41. SETTINGS

Settings should include:

- LLM provider
- Model
- Temperature
- Maximum tokens
- Voice
- Microphone
- Speaker
- Wake word
- Language
- Theme
- Memory
- Privacy
- Tool permissions
- Confirmation behavior
- Offline mode
- Logging level

---

# 42. PRIVACY MODE

Add a privacy mode.

When enabled:

- Disable cloud services where possible
- Prefer local models
- Disable unnecessary telemetry
- Minimize logging
- Provide clear status

---

# 43. PERSONALITY

AJAX should be:

- Intelligent
- Helpful
- Natural
- Professional
- Friendly
- Concise when possible
- Detailed when necessary
- Honest about limitations

AJAX must never claim an action was successful if the tool failed.

---

# 44. RESPONSE STYLE

For commands:

```text
User:
Open Chrome.

AJAX:
Opening Chrome.
```

For complex tasks:

```text
AJAX:
I found 18 large files.

Largest:
1. ...
2. ...
3. ...

I have not deleted anything.
```

For failures:

```text
AJAX:
I couldn't complete that action because Chrome is not installed at the detected location.
```

---

# 45. UI

Create a professional AI interface.

Required:

- Sidebar
- Chat
- Voice button
- Input box
- Conversation history
- Settings
- Memory
- Tools
- Model information
- System status
- Training dashboard
- Logs
- Diagnostics

Support:

- Dark mode
- Light mode
- Responsive layout
- Keyboard shortcuts
- Accessibility

Avoid excessive animations.

---

# 46. STREAMING

LLM responses should stream when supported.

UI must support:

- Start stream
- Stop
- Retry
- Error recovery

---

# 47. PERFORMANCE

Optimize:

- Startup
- Model loading
- Memory usage
- CPU usage
- GPU usage
- Voice processing
- LLM latency
- Database queries

Use:

- Async
- Threading
- Caching
- Lazy loading
- Background workers

where appropriate.

Never freeze the UI during long operations.

---

# 48. LOGGING

Use structured logging.

Files:

```text
logs/
ajax.log
error.log
security.log
tools.log
voice.log
training.log
```

Track:

- Request
- Intent
- Confidence
- Tool
- Result
- Latency
- Error

Do not log secrets.

---

# 49. ERROR HANDLING

Handle gracefully:

- API timeout
- API quota
- Invalid API key
- Network failure
- Model failure
- Microphone failure
- Speaker failure
- File permission
- Missing application
- Database error
- Corrupt model
- Plugin failure

AJAX must continue operating wherever possible.

---

# 50. TESTING

Create comprehensive tests.

Test:

- LLM provider
- Intent model
- Confidence
- Router
- Tools
- Safety
- Memory
- Database
- Voice
- TTS
- RAG
- Plugins
- PC commands
- Error handling
- Fallback

Use:

```text
tests/
```

with unit and integration tests.

---

# 51. SECURITY TESTING

Test:

- Prompt injection
- Tool injection
- Path traversal
- Arbitrary command execution
- Malicious filenames
- Unauthorized tools
- Permission bypass
- Plugin abuse

Never trust LLM output as executable code.

---

# 52. DOCUMENTATION

Generate:

```text
README.md
INSTALLATION.md
CONFIGURATION.md
ARCHITECTURE.md
SECURITY.md
VOICE.md
TRAINING.md
PLUGINS.md
TOOLS.md
TROUBLESHOOTING.md
```

Explain everything clearly.

---

# 53. PROJECT STRUCTURE

Adapt this structure to the existing project:

```text
AJAX_AI/
│
├── main.py
├── config.py
├── requirements.txt
├── .env.example
├── README.md
│
├── core/
│   ├── assistant.py
│   ├── router.py
│   ├── planner.py
│   ├── context.py
│   ├── safety.py
│   ├── permissions.py
│   └── events.py
│
├── ai/
│   ├── llm/
│   ├── neural/
│   ├── rag/
│   ├── vision/
│   └── embeddings/
│
├── memory/
│
├── voice/
│
├── tools/
│
├── plugins/
│
├── browser/
│
├── system/
│
├── database/
│
├── training/
│
├── models/
│
├── data/
│
├── ui/
│
├── tests/
│
├── logs/
│
└── backups/
```

---

# 54. STARTUP FLOW

On startup:

```text
Load configuration
↓
Validate environment
↓
Initialize database
↓
Load memory
↓
Load LLM
↓
Load Neural Network
↓
Register tools
↓
Load plugins
↓
Initialize voice
↓
Initialize UI
↓
Run health checks
↓
Start AJAX
```

Optional services must not prevent startup of core services.

---

# 55. CLI

Support:

```bash
python main.py
```

Commands:

```text
/chat
/voice
/model
/train
/evaluate
/memory
/tools
/plugins
/status
/diagnostics
/settings
/help
/exit
```

---

# 56. API

Create optional local API.

Example:

```text
POST /chat
POST /voice
GET /status
GET /memory
POST /tools
GET /models
```

Secure the API.

Do not expose dangerous tools without authentication/permission.

---

# 57. EXTENSIBILITY

AJAX should be designed so future features can be added without rewriting the core.

Possible future modules:

- Calendar
- Email
- Smart home
- Mobile app
- Android companion
- IoT
- Robotics
- Advanced vision
- Local multimodal models

---

# 58. DEVELOPMENT WORKFLOW

Before coding:

1. Inspect project
2. Map architecture
3. List current features
4. List dependencies
5. Identify conflicts
6. Identify reusable code
7. Create migration plan

Then implement incrementally.

After every phase:

- Run tests
- Run application
- Verify existing features
- Fix regressions

Never make a huge unverified rewrite.

---

# 59. FINAL ACCEPTANCE TEST

AJAX is considered complete only when all of the following work:

### Chat

```text
User → Chat → AJAX → LLM → Response
```

### Voice

```text
User → Microphone → STT → AJAX → TTS → Speaker
```

### Neural Network

```text
Input → Intent → Confidence → Router
```

### Memory

```text
Conversation → Memory → Retrieval → Context
```

### RAG

```text
Document → Embedding → Retrieval → LLM
```

### PC

```text
Request → Tool → Safety → Execution → Result
```

### Learning

```text
Interaction → Dataset → Training → Evaluation → Model
```

### Offline

```text
Internet unavailable
↓
Local LLM / Neural Network / Legacy commands
```

### Security

```text
Every action
↓
Permission
↓
Validation
↓
Confirmation if required
↓
Execution
```

---

# 60. MOST IMPORTANT RULE

Do not implement a fake "AI".

Do not create a simple keyword-based bot and call it a neural network.

Do not create a fake ChatGPT clone.

Use a real LLM/Transformer for advanced language understanding.

Use Neural Networks/embeddings for classification and semantic understanding.

Use tools for real-world actions.

Use memory for personalization.

Use RAG for external/local knowledge.

Use voice models for speech.

Use safety and permission layers for PC control.

Use controlled training for learning.

---

# 61. FINAL OBJECTIVE

The final AJAX AI should behave like a powerful personal AI operating layer:

```text
                 ┌───────────────────┐
                 │      AJAX AI      │
                 │                   │
                 │  LLM + ML + RAG   │
                 │  Memory + Vision  │
                 │  Voice + Tools    │
                 └─────────┬─────────┘
                           │
              ┌────────────┼────────────┐
              ↓            ↓            ↓
           CHAT          VOICE        VISION
              │            │            │
              └────────────┼────────────┘
                           ↓
                     AI BRAIN
                           ↓
                    AGENT PLANNER
                           ↓
                     TOOL ROUTER
                           ↓
       ┌──────────┬────────┼────────┬──────────┐
       ↓          ↓        ↓        ↓          ↓
      PC        FILES     WEB      APPS      APIs
       │          │        │        │          │
       └──────────┴────────┴────────┴──────────┘
                           ↓
                     SAFETY ENGINE
                           ↓
                     ACTION RESULT
                           ↓
                    MEMORY / LEARNING
                           ↓
                     AJAX RESPONSE
```

The final system must be:

- Intelligent
- Conversational
- Multilingual
- Voice-enabled
- Vision-enabled
- Memory-enabled
- Tool-enabled
- PC-aware
- Secure
- Modular
- Extensible
- Fast
- Reliable
- Offline-capable where possible
- Production-ready

**Do not omit any requirement from this specification.**

If an existing project feature conflicts with the new architecture, preserve the feature and redesign the integration rather than deleting it.

Before declaring completion, perform a feature-by-feature audit against this entire specification and report:

```text
IMPLEMENTED
PARTIALLY IMPLEMENTED
NOT IMPLEMENTED
BLOCKED BY DEPENDENCY
```

There must be no silent omissions.

---

# 62. PHASED MASTER EXECUTION ROADMAP & DETAILED IMPLEMENTATION BLUEPRINT

This section defines the exact, non-destructive step-by-step engineering roadmap to transform the current codebase into the complete AJAX AI production system without losing any existing feature.

```text
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                               MASTER EXECUTION PHASES                                   │
├───────────────┬─────────────────┬─────────────────┬──────────────────┬──────────────────┤
│ Phase 0: Base │ Phase 1: Legacy │ Phase 2: Data & │ Phase 3: Tools & │ Phase 4: Brain & │
│ & Config      │ Code Migration  │ Storage Layer   │ Safety Engine    │ LLM Multi-Engine │
├───────────────┼─────────────────┼─────────────────┼──────────────────┼──────────────────┤
│ Phase 5: ML & │ Phase 6: Memory │ Phase 7: RAG &  │ Phase 8: Voice   │ Phase 9: Vision  │
│ Intent Engine │ Multi-Tier      │ Knowledge Base  │ Unified Pipeline │ & Screen Intel   │
├───────────────┼─────────────────┼─────────────────┼──────────────────┼──────────────────┤
│ Phase 10:     │ Phase 11: UI,   │ Phase 12: Test, │ Phase 13: Audit  │ Phase 14: Final  │
│ Agent Planner │ CLI & Local API │ Security & Docs │ & Verification   │ Release          │
└───────────────┴─────────────────┴─────────────────┴──────────────────┴──────────────────┘
```

---

## 62.1 PHASE 0: FOUNDATION, CONFIGURATION & ENVIRONMENT HARDENING

### Goals:
1. Establish robust configuration management supporting YAML/JSON and environment variables (`.env`).
2. Create modular dependency specifications in `requirements.txt` with clear separation between core, AI, voice, vision, and UI requirements.
3. Configure structured rotating logging (`core/logger.py`) across specialized log sinks (`ajax.log`, `error.log`, `security.log`, `tools.log`, `voice.log`, `training.log`).

### Target File Blueprint:
- `.env.example` — Template for API keys, model configs, and security settings.
- `config/config_loader.py` — Strongly typed configuration schema (Pydantic / dataclasses).
- `config/default_config.yaml` — Default configurations for providers, paths, thresholds, and permissions.
- `core/logger.py` — Centralized structured logging engine with redaction for sensitive keys/passwords.
- `requirements.txt` — Complete dependency manifest.

### Zero-Data Loss Check:
- Existing `data/query.txt` and legacy configs are preserved and backed up.

---

## 62.2 PHASE 1: LEGACY CODE AUDIT & ZERO-LOSS MIGRATION ADAPTER

### Existing Codebase Inventory & Migration Mapping:
| Legacy File | Current Functions | Target Modular Location | Migration Strategy |
| :--- | :--- | :--- | :--- |
| `core/tts.py` | `speak()`, `wish_user()` | `voice/tts.py` | Wrap existing `pyttsx3` into unified `TTSProvider` with async queue & fallback |
| `core/stt.py` | `take_command()` | `voice/stt.py` | Wrap `speech_recognition` into `STTProvider` with noise reduction & VAD |
| `core/memory_ops.py` | `remember_data()`, `fetch_memory()` | `memory/legacy_adapter.py` | Ingest into SQLite database while keeping text file backward compatibility |
| `commands/web_ops.py` | `search_web()`, `play_youtube()`, `get_news()` | `tools/web_tools.py` | Refactor into standardized `Tool` classes with input validation & output schema |
| `commands/system_ops.py` | `get_time()`, `get_date()`, `system_power()`, `volume_control()`, `take_screenshot()`, `open_app()`, `close_app()`, `check_battery()`, `check_cpu()` | `tools/system_tools.py` | Convert to validated system tools with permission checks (`SAFE` vs `CONFIRM_REQUIRED`) |
| `commands/app_cmd.py` & `close_cmd.py` | Application launch / kill logic | `tools/app_tools.py` | Integrate with auto-discovery application registry in `system/app_registry.py` |
| `commands/timer_ops.py` | `set_timer()`, `set_alarm()` | `system/scheduler.py` | Convert to async non-blocking background scheduler |
| `config/sites.py` | Extensive site URL dictionary | `config/sites.py` (enhanced) | Keep exact dictionary; expose to web routing tools and fast search |
| `services/weather.py` | `get_weather()` | `tools/weather_tool.py` | Wrap into `WeatherTool` with offline cache and error handling |

---

## 62.3 PHASE 2: DATA PERSISTENCE & DATABASE ARCHITECTURE

### Target File Blueprint:
- `database/db.py` — Connection manager, connection pooling, and auto-migration for SQLite.
- `database/models.py` — Tables:
  1. `conversations` (id, title, created_at, updated_at, is_archived, is_pinned)
  2. `messages` (id, conversation_id, role, content, modality, tokens, created_at)
  3. `memories` (id, category, key, value, source, confidence, created_at, updated_at)
  4. `tool_executions` (id, tool_name, parameters, result, status, duration_ms, timestamp)
  5. `training_examples` (id, raw_text, intent, entities_json, confidence, source, approved, created_at)
  6. `model_registry` (id, version, model_type, accuracy, f1_score, file_path, is_active, created_at)
  7. `scheduled_tasks` (id, task_type, target_time, recurrence, payload_json, status, created_at)
  8. `audit_logs` (id, event_type, severity, details_json, ip_address, timestamp)
- `database/crud.py` — High-performance async/sync CRUD operations.
- `database/backup.py` — Database backup, restore, and JSON export/import handlers.

---

## 62.4 PHASE 3: CENTRAL TOOL REGISTRY & SAFETY VALIDATION ENGINE

### Target File Blueprint:
- `tools/base.py` — Base `Tool` abstract class:
  - `name`: str
  - `description`: str
  - `parameters`: JSON Schema / Pydantic model
  - `permission`: `SAFE` | `CONFIRM_REQUIRED` | `BLOCKED`
  - `execute(params)` -> `ToolResult`
- `tools/registry.py` — Singleton registry with auto-discovery, enable/disable, and permission filtering.
- `core/safety.py` — Action validator:
  - Shell command allowlisting (Strict rejection of raw unrestricted shell commands)
  - Path traversal and sensitive directory protection (e.g., Windows system folders, private user data)
  - Interactive user confirmation protocol for destructive actions (File deletion, shutdown, restarts, setting changes)
- `tools/system_tools.py` — CPU, RAM, GPU, Disk, Battery, Network, Volume, Brightness, Power tools.
- `tools/file_tools.py` — Safe search, read, write, copy, move, delete (with recycle bin/backup safety).
- `tools/app_tools.py` — Application discovery, launch, status, terminate.
- `tools/web_tools.py` — Search, Wikipedia, YouTube, news, site launcher using `config/sites.py`.
- `tools/scheduler_tools.py` — Timers, alarms, reminders, scheduled tasks.

---

## 62.5 PHASE 4: AI BRAIN & MULTI-PROVIDER LLM ABSTRACTION

### Target File Blueprint:
- `ai/llm/base.py` — Standardized `LLMProvider` interface:
  - `generate(messages, tools=None, stream=False)`
  - `generate_structured(messages, schema)`
- `ai/llm/openai_provider.py` — OpenAI, Groq, DeepSeek, Together, OpenRouter, and OpenAI-compatible endpoints.
- `ai/llm/ollama_provider.py` — Local Ollama provider for offline operations.
- `ai/llm/local_transformer_provider.py` — Direct HuggingFace/GGUF/CTranslate2 local model runner.
- `ai/llm/factory.py` — Dynamic model factory based on `config.yaml` with automatic fallback.
- `core/context.py` — Context window management:
  - Rolling message history
  - Conversation compression & summarization
  - Dynamic injection of relevant memories and RAG chunks
- `core/prompts.py` — System instructions, persona, and bilingual (Hindi/English/Hinglish) formatting rules.

---

## 62.6 PHASE 5: NEURAL NETWORK INTENT ENGINE & CONTINUOUS LEARNING

### Target File Blueprint:
- `ai/neural/intent_classifier.py` — Hybrid Intent Engine:
  - Fast semantic intent detection using Sentence-Transformers / PyTorch / LightGBM.
  - Predefined intents from Section 6 with extensible custom intent support.
  - Confidence scoring (`HIGH` >= 0.85, `MEDIUM` 0.50-0.84, `LOW` < 0.50).
- `core/router.py` — Intelligent Request Router:
  - Routes `HIGH` confidence safe commands directly to Tools.
  - Routes `MEDIUM` confidence or ambiguous queries to LLM Planner / Clarification.
  - Routes `LOW` confidence or conversational inputs to LLM Brain.
  - Falls back to local neural / legacy commands when offline.
- `data/intents.json` — Comprehensive initial training dataset (English, Hindi, Hinglish variations).
- `training/train.py` — Offline/Background training script with cross-validation, loss, accuracy, F1 tracking.
- `training/evaluate.py` — Model evaluation, confusion matrix, and regression testing.
- `training/collector.py` — Candidate sample collector with user review and approval workflow.
- `models/` — Versioned model repository (`ajax_v1/`, `ajax_v2/`) with auto-rollback on failure.

---

## 62.7 PHASE 6: MULTI-TIER MEMORY ENGINE

### Target File Blueprint:
- `memory/manager.py` — Unified Memory Coordinator:
  1. **Short-Term Memory**: Fast in-memory deque of current session turns.
  2. **Long-Term Memory**: Persistent user facts, preferences, and explicitly saved notes stored in SQLite.
  3. **Episodic Memory**: History of past tasks, successes, tool outputs, and user feedback.
  4. **Semantic Memory**: Embedding-based vector index for semantic similarity search over memories.
- `ai/embeddings/embedder.py` — Fast local/remote embedding generator (e.g., `all-MiniLM-L6-v2` or API).
- `memory/privacy.py` — Automatic filter to reject storing sensitive credentials, API keys, passwords, or credit card numbers.

---

## 62.8 PHASE 7: RETRIEVAL-AUGMENTED GENERATION (RAG) SUBSYSTEM

### Target File Blueprint:
- `ai/rag/loader.py` — Document parsers for PDF, TXT, Markdown, DOCX, and Code files.
- `ai/rag/chunker.py` — Recursive character and semantic markdown chunking with token overlaps.
- `ai/rag/vector_store.py` — Local vector store (ChromaDB / FAISS / SQLite-Vec / numpy vector index) with persistent storage in `data/vector_store/`.
- `ai/rag/pipeline.py` — End-to-end RAG query pipeline with similarity score thresholding and exact source citations.

---

## 62.9 PHASE 8: VOICE AI & UNIFIED AUDIO PIPELINE

### Target File Blueprint:
- `voice/wake_word.py` — Lightweight, low-CPU wake word detector (configurable: "AJAX", "Jarvis") with background listening.
- `voice/vad.py` — Voice Activity Detection & WebRTC / Silero silence detector to eliminate background noise.
- `voice/stt.py` — Pluggable Speech-to-Text:
  - Local: Faster-Whisper / Vosk / SpeechRecognition
  - Cloud: Whisper API / Google STT
- `voice/tts.py` — Pluggable Text-to-Speech:
  - Local: `pyttsx3` / Edge-TTS / Coqui-TTS
  - Support for interruptibility (immediate stop on user speech), volume, rate, and voice profile selection.
- `voice/manager.py` — Voice session coordinator connecting microphone/speaker directly to the same unified AI Brain pipeline as Chat.

---

## 62.10 PHASE 9: COMPUTER VISION & SCREEN INTELLIGENCE

### Target File Blueprint:
- `ai/vision/analyzer.py` — Multimodal vision adapter supporting GPT-4o, Claude 3.5 Sonnet, Gemini 1.5/2.0, Ollama LLaVA/Moondream.
- `ai/vision/ocr.py` — Local OCR (Tesseract / EasyOCR) for text and error log extraction from images.
- `ai/vision/screen.py` — Safe screenshot grabber and UI bounding-box analyzer for screen understanding.
- `ai/vision/action.py` — Supervised UI navigation actions with explicit safety confirmation for high-impact clicks.

---

## 62.11 PHASE 10: AUTONOMOUS AGENT PLANNER & SYSTEM MANAGEMENT

### Target File Blueprint:
- `core/planner.py` — ReAct (Reason + Act) autonomous planning engine:
  - Multi-step task decomposition
  - Dynamic tool invocation loop
  - Maximum step limit guardrails (preventing infinite loops)
  - Observation feedback loop and error self-correction
- `system/monitor.py` — Real-time telemetry: CPU, RAM, GPU, Disk, Battery, Network, Processes, and temperatures.
- `system/scheduler.py` — Async background job scheduler for recurring alarms, reminders, and automated health checks.
- `core/diagnostics.py` — Comprehensive self-diagnostic suite (`/health`, `/diagnostics`, `/status`).

---

## 62.12 PHASE 11: USER INTERFACES (CLI, LOCAL REST API & MODERN GUI)

### Target File Blueprint:
- `main.py` — Unified entry point supporting CLI mode, Voice mode, GUI mode, and API mode.
- `ui/cli.py` — Interactive rich command-line interface with all slash commands:
  - `/chat`, `/voice`, `/model`, `/train`, `/evaluate`, `/memory`, `/tools`, `/plugins`, `/status`, `/diagnostics`, `/settings`, `/help`, `/exit`.
- `api/server.py` — FastAPI local secure server providing REST and WebSocket endpoints:
  - `POST /api/chat` (with streaming support)
  - `POST /api/voice`
  - `GET /api/status`
  - `GET /api/memory`
  - `POST /api/tools/execute`
- `ui/web/` / `ui/gui.py` — Modern glassmorphic, dark-mode desktop/web interface featuring live chat, voice visualizer, memory manager, diagnostics dashboard, training visualizer, and settings editor.

---

## 62.13 PHASE 12: PLUGIN SYSTEM & EXTENSIBILITY

### Target File Blueprint:
- `plugins/base.py` — Plugin interface and manifest parser (`plugin.json`).
- `plugins/manager.py` — Plugin loader with sandbox permissions and lifecycle hooks (`on_load`, `on_unload`, `register_tools`).
- Built-in initial plugins:
  - `plugins/weather/`
  - `plugins/calculator/`
  - `plugins/productivity/`
  - `plugins/custom/`

---

## 62.14 PHASE 13: TESTING, SECURITY VERIFICATION & DOCUMENTATION

### Target File Blueprint:
- `tests/unit/` — Unit tests for LLM providers, intent engine, memory manager, safety filters, database CRUD, and tools.
- `tests/integration/` — End-to-end multi-turn chat, voice STT->Brain->TTS pipeline, RAG document query, and task planner.
- `tests/security/` — Penetration tests against prompt injection, path traversal, unauthorized shell execution, and sensitive data leakage.
- Documentation suite:
  - `README.md` — Project overview, architecture, quick start.
  - `INSTALLATION.md` — Complete setup guide for Windows, Python virtual environments, and optional local AI dependencies.
  - `ARCHITECTURE.md` — Detailed system diagrams, data flow, and component relationships.
  - `TOOLS.md` — Catalog of all built-in tools, parameters, and permission levels.
  - `SECURITY.md` — Safety policies, permission models, and data privacy guarantees.
  - `VOICE.md` — Voice configuration, wake word setup, and audio troubleshooting.
  - `TRAINING.md` — Intent model training, dataset curation, and evaluation guide.
  - `PLUGINS.md` — Plugin development guide and API reference.
  - `TROUBLESHOOTING.md` — Common errors, recovery steps, and diagnostic guide.

---

## 62.15 PHASE 14: MASTER COMPLIANCE & ACCEPTANCE CHECKLIST

Before final sign-off, every feature below must be verified and marked **IMPLEMENTED**:

| # | System Module | Core Features to Verify | Status Requirement |
| :- | :--- | :--- | :--- |
| 1 | **AI Brain & LLM** | Multi-provider support, streaming, structured output, fallback chain | `IMPLEMENTED` |
| 2 | **Neural Intent Engine** | 40+ default intents, confidence scoring, router, continuous training | `IMPLEMENTED` |
| 3 | **Voice AI** | Wake word, noise reduction, VAD, STT, interruptible TTS | `IMPLEMENTED` |
| 4 | **Memory System** | Short-term, long-term, episodic, semantic vector memory, memory UI | `IMPLEMENTED` |
| 5 | **RAG System** | Document ingestion (PDF/TXT/DOCX/Code), vector search, cited answers | `IMPLEMENTED` |
| 6 | **PC & System Control** | App launcher, system metrics, volume/brightness, power controls | `IMPLEMENTED` |
| 7 | **Safety Engine** | Strict command allowlist, path protection, user confirmation prompts | `IMPLEMENTED` |
| 8 | **Vision & Screen** | Image reasoning, OCR, screenshot UI analysis | `IMPLEMENTED` |
| 9 | **Agent Planner** | Multi-step task decomposition, step limits, observation loop | `IMPLEMENTED` |
| 10 | **Offline Fallback** | Seamless degradation from Cloud LLM -> Local LLM -> Neural Model -> Legacy Commands | `IMPLEMENTED` |
| 11 | **User Interfaces** | CLI slash commands, REST API, modern responsive UI | `IMPLEMENTED` |
| 12 | **Documentation & Tests** | Complete markdown documentation suite, unit, integration, and security tests | `IMPLEMENTED` |