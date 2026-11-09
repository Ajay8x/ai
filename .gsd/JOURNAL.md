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
