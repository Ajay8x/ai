"""
AJAX AI - Document Loader & Chunker for RAG
Extracts text from PDF, TXT, Markdown, DOCX, and Code files.
"""

import os
import re
from typing import List

class DocumentLoader:
    @staticmethod
    def load_file(file_path: str) -> str:
        if not os.path.exists(file_path):
            return ""
            
        ext = os.path.splitext(file_path)[1].lower()
        if ext in [".txt", ".md", ".py", ".json", ".csv", ".yaml", ".yml", ".html", ".js", ".ts", ".css"]:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
        elif ext == ".pdf":
            try:
                import pypdf
                reader = pypdf.PdfReader(file_path)
                return "\n\n".join([f"[Page {i+1}]\n{page.extract_text() or ''}" for i, page in enumerate(reader.pages)])
            except Exception as e:
                return ""
        elif ext in [".docx", ".doc"]:
            try:
                import docx
                doc = docx.Document(file_path)
                return "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
            except Exception:
                return ""
        return ""

    @staticmethod
    def chunk_text(text: str, chunk_size: int = 700, overlap: int = 100) -> List[str]:
        """Split text on paragraph boundaries while preserving overlap for retrieval."""
        if not text:
            return []

        if chunk_size <= 0:
            raise ValueError("chunk_size must be positive")
        overlap = max(0, min(overlap, chunk_size // 3))

        normalized = text.replace("\r\n", "\n").replace("\r", "\n")
        blocks = [
            re.sub(r"[ \t]+", " ", block).strip()
            for block in re.split(r"\n\s*\n", normalized)
            if block.strip()
        ]

        chunks = []
        current = ""

        def flush_current():
            nonlocal current
            if current.strip():
                chunks.append(current.strip())
            current = ""

        for block in blocks:
            if len(block) <= chunk_size:
                candidate = f"{current}\n\n{block}".strip() if current else block
                if len(candidate) <= chunk_size:
                    current = candidate
                else:
                    flush_current()
                    current = block
                continue

            flush_current()
            start = 0
            while start < len(block):
                end = min(start + chunk_size, len(block))
                if end < len(block):
                    boundary = max(block.rfind(" ", start, end), block.rfind("\n", start, end))
                    if boundary > start + (chunk_size // 2):
                        end = boundary
                piece = block[start:end].strip()
                if piece:
                    chunks.append(piece)
                if end >= len(block):
                    break
                start = max(end - overlap, start + 1)

        flush_current()
        return chunks

doc_loader = DocumentLoader()
