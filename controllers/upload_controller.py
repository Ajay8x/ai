"""
AJAX AI - MVC Controller: Document Upload & RAG Processing
"""

import os
import base64
import binascii
import re
import uuid
from pathlib import Path, PurePosixPath
from typing import Dict, Any, Tuple
from fastapi import APIRouter, Depends, HTTPException
from models.schemas import UploadRequest, UploadResponse
from ai.rag.store import rag_store
from config.config_loader import config
from core.logger import ajax_logger, error_logger
from controllers.auth_controller import require_authenticated_user

upload_router = APIRouter(prefix="/api", tags=["Document Processing & RAG"])

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOAD_DIR = os.path.join(BASE_DIR, "data", "uploads")
if os.environ.get("VERCEL") or os.environ.get("AWS_LAMBDA_FUNCTION_NAME"):
    UPLOAD_DIR = os.path.join("/tmp", "ajax_uploads")

try:
    os.makedirs(UPLOAD_DIR, exist_ok=True)
except OSError:
    pass

UPLOAD_ROOT = Path(UPLOAD_DIR).resolve()
ALLOWED_UPLOAD_EXTENSIONS = {
    ".txt", ".md", ".py", ".json", ".csv", ".yaml", ".yml",
    ".html", ".js", ".ts", ".css", ".pdf", ".docx", ".doc"
}


def _build_safe_upload_path(filename: str) -> Tuple[Path, str]:
    """Return a randomized path guaranteed to remain inside the upload root."""
    if not filename or "\x00" in filename:
        raise HTTPException(status_code=400, detail="Invalid filename.")

    # Normalize both Windows and POSIX separators before taking the basename.
    original_name = PurePosixPath(filename.replace("\\", "/")).name.strip()
    if not original_name or original_name in {".", ".."}:
        raise HTTPException(status_code=400, detail="Invalid filename.")
    if len(original_name) > 255:
        raise HTTPException(status_code=400, detail="Filename is too long.")

    extension = Path(original_name).suffix.lower()
    if extension not in ALLOWED_UPLOAD_EXTENSIONS:
        allowed = ", ".join(sorted(ALLOWED_UPLOAD_EXTENSIONS))
        raise HTTPException(status_code=415, detail=f"Unsupported file type. Allowed extensions: {allowed}")

    stem = Path(original_name).stem
    safe_stem = re.sub(r"[^A-Za-z0-9._-]+", "_", stem).strip("._") or "upload"
    stored_name = f"{uuid.uuid4().hex}_{safe_stem[:80]}{extension}"
    candidate = (UPLOAD_ROOT / stored_name).resolve()

    # Defense in depth: reject any path that escapes the resolved upload root.
    if candidate.parent != UPLOAD_ROOT:
        raise HTTPException(status_code=400, detail="Unsafe upload path.")

    return candidate, original_name

@upload_router.post("/upload", response_model=UploadResponse)
async def upload_document(req: UploadRequest, current_user: Dict[str, Any] = Depends(require_authenticated_user)):
    if not req.content_base64:
        raise HTTPException(status_code=400, detail="No base64 file content provided.")
    try:
        file_path_obj, original_filename = _build_safe_upload_path(req.filename)
        encoded_content = req.content_base64
        if encoded_content.startswith("data:") and "," in encoded_content:
            encoded_content = encoded_content.split(",", 1)[1]
        try:
            file_bytes = base64.b64decode(encoded_content, validate=True)
        except (binascii.Error, ValueError):
            raise HTTPException(status_code=400, detail="Invalid base64 file content.")
        if not file_bytes:
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")

        max_bytes = config.max_upload_size_mb * 1024 * 1024
        if len(file_bytes) > max_bytes:
            actual_mb = len(file_bytes) / (1024 * 1024)
            raise HTTPException(
                status_code=413,
                detail=f"File exceeds maximum upload limit of {config.max_upload_size_mb} MB (Your file is {actual_mb:.2f} MB)."
            )

        file_path = str(file_path_obj)
        with open(file_path_obj, "xb") as f:
            f.write(file_bytes)

        # Cloudinary cloud backup if configured
        cloud_url = None
        if config.cloud_name and config.cloud_api_key and config.cloud_api_secret:
            try:
                import cloudinary
                import cloudinary.uploader
                cloudinary.config(
                    cloud_name=config.cloud_name,
                    api_key=config.cloud_api_key,
                    api_secret=config.cloud_api_secret
                )
                upload_res = cloudinary.uploader.upload(
                    file_path,
                    resource_type="auto",
                    folder="ajax_ai_uploads",
                    use_filename=True,
                    unique_filename=False
                )
                cloud_url = upload_res.get("secure_url")
                ajax_logger.info(f"File uploaded to Cloudinary: {cloud_url}")
            except Exception as ce:
                ajax_logger.warning(f"Cloudinary upload skipped or failed: {ce}")
        
        # Index document into RAG vector store
        rag_store.index_file(file_path)
        chunks_count = sum(1 for d in rag_store.documents if d.get("source") == file_path)
        
        ajax_logger.info(f"Uploaded and indexed '{original_filename}' with {chunks_count} chunks.")
        msg = f"Document '{original_filename}' indexed successfully."
        if cloud_url:
            msg += f" Stored in Cloudinary ({cloud_url})."
        return {
            "success": True,
            "filename": original_filename,
            "chunks": chunks_count,
            "message": msg
        }
    except HTTPException:
        raise
    except Exception as e:
        error_logger.error(f"Failed to process file upload: {e}")
        raise HTTPException(status_code=500, detail=str(e))
