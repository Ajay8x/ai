# AJAX AI ⚡

AJAX AI is a local-first autonomous assistant with a FastAPI web dashboard, multilingual chat, voice controls, neural intent routing, document RAG, system tools, memory, and a Windows portable build.

## What is included

- **Merged neural intent catalog:** 92 active intent classes with English, Hindi, and Hinglish examples. Overlapping labels were merged while keeping their useful training phrases.
- **Local AI brain:** AJAX GGUF generation plus the AJAX Native PyTorch neural router. The Settings page exposes AJAX-local choices only.
- **Local model runtime:** AJAX Chat Core uses the bundled quantized `.gguf` model. The intent classifier can use the exported `.onnx` graph through ONNX Runtime, with safe PyTorch fallback.
- **Chat and voice:** streamed chat, session history, browser voice typing, optional speech output, and safe tool execution.
- **RAG document questions:** upload a document from the Chat paperclip or from **Documents & RAG**, index it, and ask questions with source-grounded retrieval.
- **System tools:** diagnostics, hardware telemetry, web search, calculations, reminders, notes, file search, and other guarded workflows.
- **Interactive UI:** dashboard, intent catalog, neural playground, training topology, memory, system diagnostics, and settings.

## RAG document workflow

1. Open `http://127.0.0.1:8000/AJAX/chat` and click the paperclip, or open **Documents & RAG** from the left navigation.
2. Upload a supported file: `.txt`, `.md`, `.py`, `.json`, `.csv`, `.yaml`, `.yml`, `.html`, `.js`, `.ts`, `.css`, `.pdf`, or `.docx`.
3. Files are limited to **15 MB** and are indexed in the authenticated user's RAG scope.
4. Ask a question in Chat. Relevant chunks are added to the response context and source citations are returned when available.

## Start from source

Install dependencies once:

```powershell
python -m pip install -r requirements.txt
```

Optional local configuration:

```powershell
Copy-Item .env.example .env
```

Start the web app and open the browser automatically:

```powershell
python main.py --port 8000
```

Start without opening a browser:

```powershell
python main.py --no-browser --port 8000
```

Other useful modes:

```powershell
python main.py --cli
python main.py --voice
python main.py --diagnostics
```

Install optional local model runtimes when you want GGUF or ONNX support:

```powershell
python -m pip install -r requirements-optional.txt
python training/export_intent_onnx.py
```

The ONNX graph is exported from the current `models/ajax_neural_intent.pt` checkpoint and uses the same `models/vocab_metadata.json` labels. Set `NEURAL_INFERENCE_BACKEND=auto`, `pytorch`, or `onnx` in `.env`. Chat Studio now uses **AJAX Chat Core · GGUF 1.7B** as the single local generative model, while the Neural Router remains active before every response.

On Windows, double-click [`start_ajax_ai.bat`](start_ajax_ai.bat). To stop the source server, double-click [`kill_ajax_ai.bat`](kill_ajax_ai.bat).

## Portable Windows EXE

The portable build bundles the Python runtime, local models, templates, and frontend assets. Python does not need to be installed on the target laptop.

Build it on a 64-bit Windows development machine:

```powershell
build_ajax_ai.bat
```

Then share the complete folder:

```text
dist\AJAX_AI\
├── AJAX_AI.exe
├── start_ajax_ai.bat
├── kill_ajax_ai.bat
└── _internal\ ...
```

Run `dist\AJAX_AI\start_ajax_ai.bat` to start AJAX AI and open the browser. Run the bundled `kill_ajax_ai.bat` to stop it. Share the **whole `dist\AJAX_AI` folder**, not only the `.exe`; the current bundle is approximately 2.5 GB because it contains the local GGUF and PyTorch runtime.

## Validation

Run the complete automated suite:

```powershell
python -m unittest discover -s tests -v
```

Run the intent benchmark or retrain the approved dataset when needed:

```powershell
python training/evaluate.py
python training/train.py
```

The current trained metadata contains 92 class labels and 1,028 vocabulary entries. The packaged executable has also been validated with `--diagnostics` and reports a healthy intent engine, database, and tools subsystem.

## Project layout

```text
Ai full 3.0/
├── main.py                     # Web, CLI, voice, and diagnostics entry point
├── views/templates/            # Jinja UI pages
├── frontend/                   # Browser assets and shared client helpers
├── controllers/                # FastAPI routes
├── ai/neural/                  # Intent classifier and dataset loader
├── ai/rag/                     # Document parsing, chunking, and retrieval
├── models/                     # Neural checkpoint, vocabulary, and local GGUF
├── data/                       # Intent corpus, database, and runtime data
├── training/                   # Training and evaluation scripts
├── tests/                      # Automated regression tests
├── build_ajax_ai.bat           # Build portable Windows folder
├── start_ajax_ai.bat           # Start source installation
└── kill_ajax_ai.bat            # Stop source or scoped AJAX process
```

For deployment notes, see [`README-DOCKER.md`](README-DOCKER.md) and [`README-K8S.md`](README-K8S.md).
