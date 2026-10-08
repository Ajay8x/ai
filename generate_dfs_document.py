"""
AJAX AI - Detailed Functional Specification (DFS) Document Generator
Generates a comprehensive, professionally styled Microsoft Word (.docx) specification.
"""

import os
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

def set_cell_background(cell, fill_hex):
    """Set background color of a table cell."""
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    """Set padding for a cell."""
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
        node = OxmlElement(f'w:{m}')
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)

def create_dfs_document(output_path: str = "AJAX_AI_Detailed_Functional_Specification.docx"):
    doc = docx.Document()

    # Define color palette
    COLOR_PRIMARY = RGBColor(10, 25, 47)      # Deep Navy
    COLOR_SECONDARY = RGBColor(0, 150, 214)   # Vibrant Cyan-Blue
    COLOR_DARK = RGBColor(30, 41, 59)         # Dark Slate
    COLOR_MUTED = RGBColor(100, 116, 139)     # Slate Gray
    HEX_PRIMARY = "0A192F"
    HEX_SECONDARY = "0096D6"
    HEX_LIGHT_BG = "F1F5F9"
    HEX_CARD_BG = "F8FAFC"
    HEX_BORDER = "CBD5E1"

    # Set standard page margins
    sections = doc.sections
    for section in sections:
        section.top_margin = Inches(0.8)
        section.bottom_margin = Inches(0.8)
        section.left_margin = Inches(0.8)
        section.right_margin = Inches(0.8)

    # -------------------------------------------------------------
    # 1. COVER PAGE / HEADER
    # -------------------------------------------------------------
    title_p = doc.add_paragraph()
    title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title_run = title_p.add_run("⚡ AJAX AI 3.0")
    title_run.font.name = "Arial"
    title_run.font.size = Pt(28)
    title_run.font.bold = True
    title_run.font.color.rgb = COLOR_SECONDARY

    sub_p = doc.add_paragraph()
    sub_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sub_run = sub_p.add_run("Adaptive Intelligence & Autonomous eXecution")
    sub_run.font.name = "Arial"
    sub_run.font.size = Pt(15)
    sub_run.font.italic = True
    sub_run.font.color.rgb = COLOR_MUTED

    doc_type_p = doc.add_paragraph()
    doc_type_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc_type_run = doc_type_p.add_run("DETAILED FUNCTIONAL SPECIFICATION (DFS)")
    doc_type_run.font.name = "Arial"
    doc_type_run.font.size = Pt(16)
    doc_type_run.font.bold = True
    doc_type_run.font.color.rgb = COLOR_PRIMARY

    # Document Control Metadata Box
    meta_table = doc.add_table(rows=5, cols=2)
    meta_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    meta_data = [
        ("Project Name", "AJAX AI - Autonomous System & Intelligence Assistant"),
        ("Version", "3.0.0 (Production Architecture)"),
        ("Date Created", "October 2026"),
        ("Document Classification", "Core System Architectural Specification"),
        ("Supported Hardware", "Local CPU / GPU Acceleration (AMD ROCm / NVIDIA CUDA / DirectML)")
    ]
    for row_idx, (k, v) in enumerate(meta_data):
        cell_k = meta_table.cell(row_idx, 0)
        cell_v = meta_table.cell(row_idx, 1)
        cell_k.text = k
        cell_v.text = v
        set_cell_background(cell_k, HEX_LIGHT_BG)
        set_cell_background(cell_v, "FFFFFF")
        cell_k.paragraphs[0].runs[0].font.bold = True
        cell_k.paragraphs[0].runs[0].font.size = Pt(9.5)
        cell_v.paragraphs[0].runs[0].font.size = Pt(9.5)
        cell_k.width = Inches(2.2)
        cell_v.width = Inches(4.5)

    doc.add_paragraph().paragraph_format.space_after = Pt(12)

    # Helper function for Section Headings
    def add_section_header(title: str):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(16)
        p.paragraph_format.space_after = Pt(6)
        run = p.add_run(title)
        run.font.name = "Arial"
        run.font.size = Pt(15)
        run.font.bold = True
        run.font.color.rgb = COLOR_PRIMARY

    def add_sub_header(title: str):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(10)
        p.paragraph_format.space_after = Pt(4)
        run = p.add_run(title)
        run.font.name = "Arial"
        run.font.size = Pt(12)
        run.font.bold = True
        run.font.color.rgb = COLOR_SECONDARY

    def add_body_p(text: str):
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(4)
        run = p.add_run(text)
        run.font.name = "Calibri"
        run.font.size = Pt(10.5)
        run.font.color.rgb = COLOR_DARK
        return p

    # -------------------------------------------------------------
    # 2. EXECUTIVE SUMMARY & SYSTEM OVERVIEW
    # -------------------------------------------------------------
    add_section_header("1. Executive Summary & System Overview")
    add_body_p(
        "AJAX AI is a state-of-the-art autonomous personal assistant and AI execution engine designed "
        "for Windows desktop environments. It delivers zero-latency local system automation, multi-tier persistent memory, "
        "high-accuracy neural intent routing, local RAG vector document search, and flexible multi-provider LLM brains."
    )
    add_body_p(
        "Key architectural principles include zero-cloud lock-in, hybrid offline-first execution, safety sandboxing, "
        "and sub-millisecond local intent routing for instant OS automation."
    )

    # -------------------------------------------------------------
    # 3. CORE ARCHITECTURE & DATA FLOW SPECIFICATIONS (DFS)
    # -------------------------------------------------------------
    add_section_header("2. System Architecture & Data Flow Specification (DFS)")
    add_body_p(
        "The AJAX AI execution pipeline processes multi-modal inputs (Voice, CLI, Web GUI, REST API) through a deterministic 4-stage cascade:"
    )

    flow_table = doc.add_table(rows=5, cols=3)
    flow_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    headers = ["Stage", "Subsystem", "Description & Latency Target"]
    for i, h in enumerate(headers):
        cell = flow_table.cell(0, i)
        cell.text = h
        set_cell_background(cell, HEX_PRIMARY)
        cell.paragraphs[0].runs[0].font.bold = True
        cell.paragraphs[0].runs[0].font.color.rgb = RGBColor(255, 255, 255)
        cell.paragraphs[0].runs[0].font.size = Pt(10)

    stages = [
        ("1. Input Ingestion", "Modality Handlers (STT, CLI, Web UI)", "Captures raw user query via voice transcription or text input. Modality tagging & session context enrichment (<10ms)."),
        ("2. Neural Intent & Entity Extraction", "PyTorch Cosine Intent Engine", "Classifies intent into 20+ categories, calculates confidence score (0.0 to 1.0), and extracts named entities (<5ms)."),
        ("3. Fast-Path Direct Execution", "Sandboxed Tool Registry", "If Intent Confidence >= 0.85 and tool is mapped, executes OS tool directly with zero LLM overhead (<15ms)."),
        ("4. Cognitive LLM Brain & RAG", "Llamafile / GGUF / HuggingFace / Cloud", "If complex reasoning is needed, queries RAG Vector Store and streams prompt to local Qwen LLM or Cloud provider.")
    ]
    for row_idx, (stg, sub, desc) in enumerate(stages, start=1):
        c0 = flow_table.cell(row_idx, 0)
        c1 = flow_table.cell(row_idx, 1)
        c2 = flow_table.cell(row_idx, 2)
        c0.text = stg
        c1.text = sub
        c2.text = desc
        set_cell_background(c0, HEX_LIGHT_BG if row_idx % 2 == 0 else "FFFFFF")
        set_cell_background(c1, HEX_LIGHT_BG if row_idx % 2 == 0 else "FFFFFF")
        set_cell_background(c2, HEX_LIGHT_BG if row_idx % 2 == 0 else "FFFFFF")
        c0.paragraphs[0].runs[0].font.bold = True
        c0.paragraphs[0].runs[0].font.size = Pt(9.5)
        c1.paragraphs[0].runs[0].font.size = Pt(9.5)
        c2.paragraphs[0].runs[0].font.size = Pt(9)
        c0.width = Inches(1.8)
        c1.width = Inches(1.8)
        c2.width = Inches(3.2)

    # -------------------------------------------------------------
    # 4. MODULE-BY-MODULE FILE AUDIT & INVENTORY
    # -------------------------------------------------------------
    add_section_header("3. Complete Module-by-Module File Audit & Functionality")
    add_body_p(
        "Below is the complete architectural directory tree and functional responsibility of every single file in the AJAX AI codebase:"
    )

    module_table = doc.add_table(rows=1, cols=3)
    module_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    mod_headers = ["File / Subsystem Path", "Category", "Functional Role & Responsibilities"]
    for i, h in enumerate(mod_headers):
        cell = module_table.cell(0, i)
        cell.text = h
        set_cell_background(cell, HEX_PRIMARY)
        cell.paragraphs[0].runs[0].font.bold = True
        cell.paragraphs[0].runs[0].font.color.rgb = RGBColor(255, 255, 255)
        cell.paragraphs[0].runs[0].font.size = Pt(10)

    modules_data = [
        ("main.py", "Entry Point", "Master application launcher supporting CLI, --voice, --gui, --server, and --diagnostics modes."),
        ("core/router.py", "Core Kernel", "Main orchestration engine routing requests between Direct Tools, RAG, and LLM providers."),
        ("core/context.py", "Core Kernel", "Maintains dynamic conversational history, short-term memory, and session context."),
        ("core/diagnostics.py", "Core Kernel", "Automated self-test & health check suite across Database, Tools, LLMs, and Voice."),
        ("core/logger.py", "Core Kernel", "Multi-sink logging framework recording to console and specialized log files."),
        ("core/permissions.py", "Security", "Role-based tool access permissions (SAFE, SYSTEM_READ, DESTRUCTIVE, PRIVILEGED)."),
        ("core/safety.py", "Security", "Security sandbox enforcing command blacklists, System32 protection, and validation."),
        ("ai/neural/intent_classifier.py", "AI Engine", "Fast TF-IDF / Bag-of-Words cosine intent classifier for sub-millisecond routing."),
        ("ai/neural/model.py", "AI Engine", "PyTorch Neural Network architecture (AJAXIntentNet) for deep intent classification."),
        ("ai/llm/factory.py", "LLM Layer", "Multi-tier LLM Provider manager with automatic failover across Llamafile, GGUF, HF, and Cloud."),
        ("ai/llm/llamafile_provider.py", "LLM Layer", "High-speed standalone Mozilla Llamafile server for Qwen3-4B Thinking GGUF model."),
        ("ai/llm/gguf_provider.py", "LLM Layer", "Direct in-process llama-cpp-python provider for quantized .gguf models."),
        ("ai/llm/local_hf_provider.py", "LLM Layer", "PyTorch Transformers provider for locally downloaded Qwen3.5-9B safetensors."),
        ("ai/llm/openai_provider.py", "LLM Layer", "Universal OpenAI-compatible client for Groq, DeepSeek, OpenRouter, and OpenAI."),
        ("ai/llm/ollama_provider.py", "LLM Layer", "Local Ollama REST bridge supporting Llama 3, Mistral, and Phi models."),
        ("ai/rag/store.py", "RAG Engine", "In-memory tokenized vector store for instant semantic retrieval of knowledge files."),
        ("ai/rag/loader.py", "RAG Engine", "Document parser reading TXT, MD, and PDF files with intelligent chunking."),
        ("ai/vision/screen.py", "Vision AI", "Screen capture, OCR, and visual context analysis engine."),
        ("tools/registry.py", "Tools Engine", "Central registry managing tool registration, schema validation, and safe execution."),
        ("tools/system_tools.py", "Tools", "System telemetry, volume control, screenshot capture, and power commands."),
        ("tools/app_tools.py", "Tools", "Application launcher & process terminator for Windows desktop apps."),
        ("tools/web_tools.py", "Tools", "DuckDuckGo web search, Wikipedia summary scraper, and YouTube player."),
        ("tools/weather_tool.py", "Tools", "Real-time meteorological forecast provider with caching."),
        ("tools/file_tools.py", "Tools", "Sandboxed file search, content reader, and safe deletion manager."),
        ("tools/memory_tools.py", "Tools", "Explicit user memory store and recall tools."),
        ("tools/scheduler_tools.py", "Tools", "Background threaded timer and alarm scheduler with sound alerts."),
        ("database/db.py", "Database", "SQLite schema manager initializing 8 core tables with foreign keys and indexes."),
        ("database/crud.py", "Database", "CRUD data access layer for conversations, messages, memories, and training samples."),
        ("voice/manager.py", "Voice Engine", "Full-duplex voice loop coordinating Wake Word detection, STT, and TTS output."),
        ("voice/tts.py", "Voice Engine", "High-speed text-to-speech engine using pyttsx3 with pitch and volume adjustment."),
        ("voice/stt.py", "Voice Engine", "Speech-to-text transcription engine using SpeechRecognition and Google STT."),
        ("voice/wake_word.py", "Voice Engine", "Continuous audio stream listener for wake word activation ('ajax')."),
        ("api/server.py", "Web / API", "Zero-dependency HTTP server hosting REST APIs and glowing neon Web GUI Dashboard."),
        ("ui/cli.py", "User Interface", "Rich terminal CLI with streaming responses, slash commands, and status bars."),
        ("training/train.py", "Training Suite", "PyTorch neural training script compiling intents into ajax_neural_intent.pt."),
        ("training/gpu_train.py", "Training Suite", "DirectML / CUDA GPU-accelerated training pipeline for AMD/NVIDIA GPUs."),
        ("training/stream_large_datasets.py", "Training Suite", "Large-scale knowledge base streaming & RAG vector ingestion engine."),
        ("training/ingest_wikipedia_dump.py", "Training Suite", "Wikimedia REST API article streamer for offline knowledge store.")
    ]

    for file_path, category, description in modules_data:
        row = module_table.add_row()
        c0, c1, c2 = row.cells
        c0.text = file_path
        c1.text = category
        c2.text = description
        set_cell_background(c0, HEX_LIGHT_BG)
        set_cell_background(c1, HEX_LIGHT_BG)
        set_cell_background(c2, "FFFFFF")
        c0.paragraphs[0].runs[0].font.bold = True
        c0.paragraphs[0].runs[0].font.size = Pt(9)
        c1.paragraphs[0].runs[0].font.size = Pt(9)
        c2.paragraphs[0].runs[0].font.size = Pt(9)
        c0.width = Inches(1.8)
        c1.width = Inches(1.4)
        c2.width = Inches(3.6)

    # -------------------------------------------------------------
    # 5. REGISTERED TOOLS & CAPABILITIES SPECIFICATION
    # -------------------------------------------------------------
    add_section_header("4. Registered Tools & Safety Permission Matrix")
    add_body_p("AJAX AI registers 21 specialized automation tools classified under strict safety boundaries:")

    tool_table = doc.add_table(rows=1, cols=4)
    tool_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    t_headers = ["Tool Name", "Category", "Permission", "Functionality"]
    for i, h in enumerate(t_headers):
        cell = tool_table.cell(0, i)
        cell.text = h
        set_cell_background(cell, HEX_PRIMARY)
        cell.paragraphs[0].runs[0].font.bold = True
        cell.paragraphs[0].runs[0].font.color.rgb = RGBColor(255, 255, 255)
        cell.paragraphs[0].runs[0].font.size = Pt(9.5)

    tools_spec = [
        ("get_system_time", "SYSTEM", "SAFE", "Returns live local system date, time, and timezone."),
        ("get_system_status", "SYSTEM", "SAFE", "Telemetry for CPU load, RAM usage, Disk free space, and Battery status."),
        ("control_volume", "SYSTEM", "SYSTEM_CONTROL", "Controls audio master volume (mute, unmute, set percentage level)."),
        ("take_screenshot", "SYSTEM", "SYSTEM_READ", "Captures desktop screen and saves timestamped image to disk."),
        ("system_power", "SYSTEM", "DESTRUCTIVE", "Executes system power states (shutdown, restart, sleep, lock screen)."),
        ("open_application", "APP", "SYSTEM_CONTROL", "Launches installed desktop programs (Chrome, VS Code, Notepad, etc.)."),
        ("close_application", "APP", "SYSTEM_CONTROL", "Terminates running applications cleanly via process manager."),
        ("search_web", "WEB", "SAFE", "Queries live internet search engines for instant real-time answers."),
        ("search_wikipedia", "WEB", "SAFE", "Retrieves factual encyclopedia article summaries from Wikipedia."),
        ("play_youtube", "WEB", "SAFE", "Searches and autoplays requested songs or video content on YouTube."),
        ("open_website", "WEB", "SAFE", "Opens target URLs in the user's default web browser."),
        ("get_weather", "WEB", "SAFE", "Fetches live weather conditions, temperatures, and forecasts."),
        ("search_files", "FILE", "SYSTEM_READ", "Scans user directories for matching filenames and extensions."),
        ("read_file", "FILE", "SYSTEM_READ", "Reads UTF-8 text contents from files with safety boundary checks."),
        ("delete_file", "FILE", "DESTRUCTIVE", "Deletes target file with mandatory confirmation safeguards."),
        ("set_timer", "SCHEDULER", "SAFE", "Spawns countdown timer with audio alert upon completion."),
        ("set_alarm", "SCHEDULER", "SAFE", "Schedules exact-time alarm with notification chime."),
        ("remember_fact", "MEMORY", "SAFE", "Persists long-term key-value memories into SQLite database."),
        ("recall_memory", "MEMORY", "SAFE", "Retrieves stored personal memories via keyword search."),
        ("query_documents", "RAG", "SAFE", "Performs semantic search across offline indexed documents."),
        ("analyze_screen", "VISION", "SAFE", "Extracts text and UI elements from active screen.")
    ]

    for name, cat, perm, fn in tools_spec:
        row = tool_table.add_row()
        c0, c1, c2, c3 = row.cells
        c0.text = name
        c1.text = cat
        c2.text = perm
        c3.text = fn
        set_cell_background(c0, HEX_LIGHT_BG)
        set_cell_background(c1, HEX_LIGHT_BG)
        set_cell_background(c2, "FEE2E2" if perm == "DESTRUCTIVE" else HEX_LIGHT_BG)
        set_cell_background(c3, "FFFFFF")
        c0.paragraphs[0].runs[0].font.bold = True
        c0.paragraphs[0].runs[0].font.size = Pt(9)
        c1.paragraphs[0].runs[0].font.size = Pt(8.5)
        c2.paragraphs[0].runs[0].font.size = Pt(8.5)
        c3.paragraphs[0].runs[0].font.size = Pt(9)
        c0.width = Inches(1.5)
        c1.width = Inches(1.1)
        c2.width = Inches(1.2)
        c3.width = Inches(3.0)

    # -------------------------------------------------------------
    # 6. DATABASE SCHEMA & STORAGE ARCHITECTURE
    # -------------------------------------------------------------
    add_section_header("5. Database Schema & Storage Architecture")
    add_body_p(
        "AJAX AI utilizes a robust SQLite relational database (data/ajax.db) comprising 8 core schemas:"
    )

    db_table = doc.add_table(rows=1, cols=3)
    db_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    db_headers = ["Table Name", "Primary Keys & Columns", "Purpose & Retention"]
    for i, h in enumerate(db_headers):
        cell = db_table.cell(0, i)
        cell.text = h
        set_cell_background(cell, HEX_PRIMARY)
        cell.paragraphs[0].runs[0].font.bold = True
        cell.paragraphs[0].runs[0].font.color.rgb = RGBColor(255, 255, 255)
        cell.paragraphs[0].runs[0].font.size = Pt(9.5)

    db_schemas = [
        ("conversations", "id (TEXT PK), title, created_at, updated_at, session_metadata", "Tracks chat sessions and context states across modalities."),
        ("messages", "id (TEXT PK), conversation_id (FK), role, content, modality, timestamp", "Full multi-turn chat history for context injection."),
        ("memories", "id (TEXT PK), key_text, value_text, category, confidence, created_at", "Long-term persistent user facts and preferences."),
        ("tool_executions", "id (TEXT PK), tool_name, parameters, result, success, duration_ms", "Audit trail for all executed system and OS commands."),
        ("intents_catalog", "id (TEXT PK), name, description, direct_tool, confirmation_required", "Persistent definitions of recognized neural intents."),
        ("training_dataset", "id (TEXT PK), raw_text, intent, entities, confidence, source", "Continuous learning repository collecting user queries."),
        ("system_events", "id (TEXT PK), event_type, severity, details, created_at", "Security boundary alerts, warnings, and diagnostic telemetry."),
        ("settings", "key (TEXT PK), value, category, updated_at", "Runtime configurations, active LLM selections, and voice parameters.")
    ]

    for tbl, cols, purp in db_schemas:
        row = db_table.add_row()
        c0, c1, c2 = row.cells
        c0.text = tbl
        c1.text = cols
        c2.text = purp
        set_cell_background(c0, HEX_LIGHT_BG)
        set_cell_background(c1, HEX_LIGHT_BG)
        set_cell_background(c2, "FFFFFF")
        c0.paragraphs[0].runs[0].font.bold = True
        c0.paragraphs[0].runs[0].font.size = Pt(9)
        c1.paragraphs[0].runs[0].font.size = Pt(8.5)
        c2.paragraphs[0].runs[0].font.size = Pt(9)
        c0.width = Inches(1.5)
        c1.width = Inches(2.3)
        c2.width = Inches(3.0)

    # -------------------------------------------------------------
    # 7. NATURAL LANGUAGE VOICE & COMMAND CHEATSHEET
    # -------------------------------------------------------------
    add_section_header("6. Natural Language & Voice Command Cheat-Sheet")
    add_body_p(
        "AJAX AI supports conversational natural language execution in both English and Hindi/Hinglish. Below is the command matrix:"
    )

    cmd_table = doc.add_table(rows=1, cols=3)
    cmd_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    cmd_headers = ["Category", "Sample Queries (English & Hinglish)", "Mapped Action"]
    for i, h in enumerate(cmd_headers):
        cell = cmd_table.cell(0, i)
        cell.text = h
        set_cell_background(cell, HEX_PRIMARY)
        cell.paragraphs[0].runs[0].font.bold = True
        cell.paragraphs[0].runs[0].font.color.rgb = RGBColor(255, 255, 255)
        cell.paragraphs[0].runs[0].font.size = Pt(9.5)

    commands_spec = [
        ("Internet & Web", "'Search what is Python', 'Google Elon Musk', 'News updates'", "Direct Web Search & Wikipedia Extraction"),
        ("Media & YouTube", "'Play Arijit Singh song', 'Play tutorial on YouTube', 'Volume up/down'", "YouTube Auto-Play & Sound Controller"),
        ("Apps & Window Control", "'Open Chrome', 'Open Settings', 'Close Tab', 'Close window'", "Process Spawner / Window Manager"),
        ("PC Diagnostics", "'Check CPU load', 'Check battery percentage', 'What is time/date'", "Live Telemetry & Diagnostics"),
        ("Timers & Alarms", "'Set a timer for 10 minutes', 'Set an alarm for 7 AM'", "Background Threaded Audio Scheduler"),
        ("Memory & Recall", "'Remember that my keys are on the table', 'What do you remember?'", "Relational Memory CRUD Store"),
        ("Power Management", "'Lock screen', 'Sleep PC', 'Shutdown computer'", "Safe Power Management with Confirmation Safeguards")
    ]

    for cat, qry, act in commands_spec:
        row = cmd_table.add_row()
        c0, c1, c2 = row.cells
        c0.text = cat
        c1.text = qry
        c2.text = act
        set_cell_background(c0, HEX_LIGHT_BG)
        set_cell_background(c1, "FFFFFF")
        set_cell_background(c2, HEX_LIGHT_BG)
        c0.paragraphs[0].runs[0].font.bold = True
        c0.paragraphs[0].runs[0].font.size = Pt(9)
        c1.paragraphs[0].runs[0].font.size = Pt(9)
        c2.paragraphs[0].runs[0].font.size = Pt(9)
        c0.width = Inches(1.5)
        c1.width = Inches(3.1)
        c2.width = Inches(2.2)

    # -------------------------------------------------------------
    # 8. VERIFICATION & DEPLOYMENT GUIDE
    # -------------------------------------------------------------
    add_section_header("7. Deployment, Health Diagnostics & Verification")
    add_body_p(
        "AJAX AI includes built-in automated diagnostics to verify the health of all subsystems before deployment:"
    )
    add_body_p("• Run Health Diagnostics: python main.py --diagnostics")
    add_body_p("• Launch Interactive CLI: python main.py")
    add_body_p("• Launch Web GUI Dashboard: python main.py --gui")
    add_body_p("• Launch Voice Mode: python main.py --voice")
    add_body_p("• Run Unit Test Suite: python -m unittest discover tests")

    # Save document
    doc.save(output_path)
    print(f"[SUCCESS] Detailed Functional Specification saved to: {output_path}")

if __name__ == "__main__":
    create_dfs_document()
