# Validation Journal

## Chat RAG upload

Validation evidence:

- `python -m unittest tests.test_chat_rag_upload -v` → 4 tests ran, all `OK`.
- `python -m unittest tests.test_ajax.TestAJAXCore.test_request_router tests.test_ajax.TestAJAXCore.test_streaming_router -v` → 2 tests ran, all `OK`.
- `python -m compileall -q core/context.py core/prompts.py ai/llm/factory.py ai/rag/store.py controllers/upload_controller.py` → completed successfully.
- Live local health check `GET http://127.0.0.1:8000/api/health` → `{"status":"healthy","database":"sqlite","database_ready":true}`.
- Direct upload/index/retrieval check → upload response reported `success: true`, `chunks: 1`; the query returned the uploaded Aurora passage with a source citation and user id `validation-user`.
- Static chat template check → upload input, upload button, status region, handler, 15 MB guard, and `/api/upload` target all present.
- Browser screenshot verification was attempted, but Windows Chrome URL detection stopped the computer-control session before a current screenshot could be captured.

Settings validation:

- `python -m unittest tests.test_settings tests.test_chat_rag_upload -v` → 6 tests ran, all `OK`.
- `python -m unittest tests.test_ajax.TestAJAXCore.test_request_router tests.test_ajax.TestAJAXCore.test_streaming_router -v` → 2 tests ran, all `OK`.
- `python -m compileall -q controllers/system_controller.py tests/test_settings.py` → completed successfully.
- Live local health check after restart → `{"status":"healthy","database_ready":true}`.

AJAX-only settings cleanup:

- `python -m unittest tests.test_settings -v` → 3 tests ran, all `OK`; external provider values are rejected and external key fields are absent from the settings page/API payload.
- `python -m unittest tests.test_chat_rag_upload tests.test_ajax.TestAJAXCore.test_request_router tests.test_ajax.TestAJAXCore.test_streaming_router -v` → 6 tests ran, all `OK`.
- `python -m compileall -q controllers/system_controller.py config/config_loader.py` → completed successfully.
- Runtime configuration check → `provider: ajax_gguf`, `model: ajax-native-1.7b-q4`; both are AJAX-local options.

100-intent classification validation (2026-11-09):

- Runtime loaded `100 intents`, `432 supplemental patterns`, and the PyTorch model with `100 classes` and `1028 vocab`.
- One representative, type-specific question per intent → `100/100` intents exercised; `92/100` classified correctly (`92.00%`).
- Representative failures: `OPEN_WEBSITE → OPEN_APPLICATION`, `MEMORY_RECALL → MEMORY_SAVE`, `QR_CODE → WRITE_CODE`, `AGE_CALCULATION → CALCULATE`, `BMI_CALCULATION → CALCULATE`, `TIP_CALCULATION → CALCULATE`, `HTML_CSS_HELP → WRITE_CODE`, and `TEST_GENERATION → WRITE_CODE`.
- Follow-up natural-language probes showed `MEMORY_RECALL`, `AGE_CALCULATION`, `TIP_CALCULATION`, and most `OPEN_WEBSITE`, `BMI_CALCULATION`, and `TEST_GENERATION` variants can pass; `HTML_CSS_HELP` consistently collided with `WRITE_CODE`, and QR/URL/internet wording needs more boundary rules.
- `test my internet` → `NETWORK_TEST` (confidence `1.000`). Direct connectivity check to `1.1.1.1:443` → `TcpTestSucceeded: True` over Wi-Fi.

Intent catalog merge and boundary routing validation (2026-11-09):

- Shared loader merged overlapping editing, planning, explanation, brainstorming, and email categories from 100 source labels into `92` active intents while retaining all unique patterns.
- Neural retraining → `2071 patterns across 92 intents`, `1028 words`, final training accuracy `99.4%`; checkpoint and metadata saved successfully.
- Boundary regression suite → `3 tests`, all `OK`.
- Focused regression suite → `12 tests`, all `OK`.
- Full test discovery → `19 tests`, all `OK`.
- One representative question for every active merged intent → `92/92`, `100.00%` classification coverage.
- `python -m compileall -q ai/neural/dataset_loader.py ai/neural/intent_classifier.py training/gpu_train.py controllers/system_controller.py` → completed successfully.
- `git diff --check` → no whitespace errors (only normal LF/CRLF conversion warnings).
- Updated server startup → `Loaded 92 intents` and `92 classes (1028 vocab)`; dashboard advertised at `http://127.0.0.1:8000/AJAX`.
- Live health check `GET http://127.0.0.1:8000/api/health` → `{"status":"healthy","service":"AJAX AI","version":"3.0.0","database_ready":true}`.

Portable Windows packaging validation (2026-11-09):

- PyInstaller `6.22.3` produced `dist/AJAX_AI/AJAX_AI.exe` successfully.
- Final portable folder size → approximately `2.50 GB`; the local 1.7B GGUF model and PyTorch runtime are included.
- Bundle metadata parity → `92` classes and `92` labels; required templates, frontend, plugins, neural checkpoint, and GGUF model are present.
- Packaged executable `AJAX_AI.exe --diagnostics` → `Overall Status: HEALTHY`, `INTENT_ENGINE: HEALTHY`, `intents_count: 92`, `DATABASE: HEALTHY`, and `TOOLS: HEALTHY`.
- Packaged server startup → `Loaded 92 intents`, `92 classes (1028 vocab)`, and dashboard URL printed successfully.
- Packaged `kill_ajax_ai.bat` → successfully stopped the packaged AJAX process; source launcher now writes a scoped `.ajax_ai.pid` for targeted stopping.
- Packaged `start_ajax_ai.bat` → points to the bundled `AJAX_AI.exe` and opens the browser; the source Python launcher remains separate at the project root.
- Distribution note → share the entire `dist/AJAX_AI` folder, not only the `.exe`; Python installation is not required, but this build targets 64-bit Windows and needs approximately 2.5 GB disk space.

Frontend and README consistency validation (2026-11-09):

- Updated the README for the current 92-class merged catalog, Chat/Documents RAG workflow, 15 MB upload limit, source launchers, and portable EXE distribution.
- Updated Documents & RAG UI with matching backend file types/size limit, keyboard selection, drag-and-drop handling, client-side validation, upload status feedback, and Enter-to-search behavior.
- Removed stale hard-coded neural metrics and unsupported accuracy claims from the Training, Brain, Dashboard, and Intent Catalog pages; training metrics now come from `/api/training/topology` when available.
- `python -m unittest discover -s tests -v` → 19 tests ran, all `OK`.
- Jinja parse check → all 13 HTML templates parsed successfully.
- Inline JavaScript syntax check → all 19 inline scripts parsed successfully with Node.
- Static feature checks → Chat upload, Documents upload, RAG limit, README portable instructions, and launcher references all present.
- `git diff --check` → no whitespace errors.
- Browser screenshot attempt → local server started and reported `Loaded 92 intents` / `92 classes (1028 vocab)`, but Windows browser automation transport closed before a screenshot could be captured.
