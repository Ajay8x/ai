"""
AJAX AI - MVC Controller: Document Upload & RAG Processing
"""

import os
import base64
from fastapi import APIRouter, HTTPException
from models.schemas import UploadRequest, UploadResponse
from ai.rag.store import rag_store
from core.logger import ajax_logger, error_logger

upload_router = APIRouter(prefix="/api", tags=["Document Processing & RAG"])

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOAD_DIR = os.path.join(BASE_DIR, "data", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

@upload_router.post("/upload", response_model=UploadResponse)
async def upload_document(req: UploadRequest):
    if not req.content_base64:
        raise HTTPException(status_code=400, detail="No base64 file content provided.")
    try:
        file_bytes = base64.b64decode(req.content_base64)
        file_path = os.path.join(UPLOAD_DIR, req.filename)
        with open(file_path, "wb") as f:
            f.write(file_bytes)
        
        # Index document into RAG vector store
        rag_store.index_file(file_path)
        chunks_count = sum(1 for d in rag_store.documents if d.get("source") == file_path)
        
        ajax_logger.info(f"Uploaded and indexed '{req.filename}' with {chunks_count} chunks.")
        return {
            "success": True,
            "filename": req.filename,
            "chunks": chunks_count,
            "message": f"Document '{req.filename}' indexed successfully."
        }
    except Exception as e:
        error_logger.error(f"Failed to process file upload: {e}")
        raise HTTPException(status_code=500, detail=str(e))
