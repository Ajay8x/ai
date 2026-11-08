# Feature Specification: Upload RAG Documents from Chat

Status: FINALIZED

## User goal

On the active `/AJAX/chat` screen, the user can upload a supported document and then ask questions answered from that document.

## Requirements

1. The chat composer exposes a visible document upload control beside the message input.
2. Uploads are limited to the document types already supported by the RAG loader and the configured 15 MB limit.
3. The UI shows upload progress/state and a success confirmation including the indexed chunk count.
4. Uploaded documents are indexed in the authenticated user's RAG scope.
5. Chat retrieval automatically includes relevant user-owned and system RAG chunks for both streamed and non-streamed chat, with source citations.
6. Existing chat, web search, voice, and session behavior remains intact.

## Acceptance criteria

- A file selected from `/AJAX/chat` is posted to `/api/upload` and a successful response is shown in the chat feed.
- A question about an uploaded text document returns text from that document and includes its source citation.
- A user's document chunks are not retrieved for a different authenticated user.
- Unsupported files and files over the configured limit are rejected before upload.
- Existing automated tests pass and a browser screenshot verifies the new composer control.
