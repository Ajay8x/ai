"""
AJAX AI - Document Loader & Chunker for RAG
Extracts text from PDF, TXT, Markdown, DOCX, and Code files.
"""

import os
from typing import List, Dict, Any

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
    def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        if not text:
            return []
        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunks.append(text[start:end])
            start += chunk_size - overlap
        return chunks

doc_loader = DocumentLoader()
