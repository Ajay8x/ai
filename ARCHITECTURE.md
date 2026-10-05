# AJAX AI - Architecture Specification

## 🏗️ High-Level System Architecture

```text
                                  ┌────────────────────────────────────────┐
                                  │                AJAX AI                 │
                                  │ Adaptive Intelligence & Autonomous     │
                                  │              eXecution                 │
                                  └───────────────────┬────────────────────┘
                                                      │
                       ┌──────────────────────────────┼──────────────────────────────┐
                       ↓                              ↓                              ↓
               [Interactive CLI]               [Voice Pipeline]             [Web UI & REST API]
                  (ui/cli.py)                 (voice/manager.py)              (api/server.py)
                       │                              │                              │
                       └──────────────────────────────┼──────────────────────────────┘
                                                      ↓
                                            ┌──────────────────┐
                                            │ REQUEST ROUTER   │
                                            │ (core/router.py) │
                                            └─────────┬────────┘
                                                      │
                       ┌──────────────────────────────┼──────────────────────────────┐
                       ↓                              ↓                              ↓
             [Neural Intent Engine]           [Context Manager]             [Multi-Tier Memory]
           (ai/neural/classifier.py)         (core/context.py)              (memory/manager.py)
                       │                              │                              │
                       └──────────────────────────────┼──────────────────────────────┘
                                                      ↓
                                            ┌──────────────────┐
                                            │     AI BRAIN     │
                                            │ (ai/llm/factory) │
                                            └─────────┬────────┘
                                                      ↓
                                            ┌──────────────────┐
                                            │  AGENT PLANNER   │
                                            │ (core/planner.py)│
                                            └─────────┬────────┘
                                                      ↓
                                            ┌──────────────────┐
                                            │  SAFETY ENGINE   │
                                            │ (core/safety.py) │
                                            └─────────┬────────┘
                                                      ↓
                                            ┌──────────────────┐
                                            │  TOOL REGISTRY   │
                                            │(tools/registry.py│
                                            └─────────┬────────┘
                                                      │
          ┌─────────────┬──────────────┬──────────────┼──────────────┬──────────────┐
          ↓             ↓              ↓              ↓              ↓              ↓
      [System]       [Apps]          [Web]         [Files]      [Scheduler]       [RAG]
     (system_tools) (app_tools)   (web_tools)    (file_tools) (scheduler_tools) (rag_tools)
```

---

## 🧩 Core Subsystems

1. **AI Brain Layer (`ai/llm/`)**:
   - `BaseLLMProvider`: Standard abstract provider interface.
   - `OpenAICompatibleProvider`: Connects with OpenAI, Groq, DeepSeek, OpenRouter, and local OpenAI-compatible APIs.
   - `OllamaProvider`: Native local model runner for offline intelligence.
   - `ResilientLLMBrain`: Cascades from primary cloud LLM to local Ollama, falling back to local rule engine when offline.

2. **Neural Intent Subsystem (`ai/neural/`)**:
   - Fast cosine token matcher with word-boundary regularization.
   - Predicts 40+ intents with confidence scores (`HIGH`, `MEDIUM`, `LOW`).

3. **Data Persistence (`database/`)**:
   - SQLite relational storage managing 8 core tables (`conversations`, `messages`, `memories`, `tool_executions`, `training_examples`, `model_registry`, `scheduled_tasks`, `audit_logs`).

4. **Safety & Guardrails (`core/safety.py`, `core/permissions.py`)**:
   - Path protection: Blocks destructive operations on critical Windows directories (`C:\Windows`, `C:\Program Files`, root drives).
   - Shell command allowlisting: Sanitizes command parameters.
   - Permission tiering: `SAFE`, `CONFIRM_REQUIRED`, and `BLOCKED`.
