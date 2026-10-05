"""
AJAX AI - Filesystem Tools
Safe file search, read, write, and directory inspection with safety guardrails.
"""

import os
import glob
from typing import Dict, Any, List, Optional
from tools.base import BaseTool, ToolResult
from core.permissions import PermissionLevel, ToolCategory
from core.safety import safety_engine

class SearchFilesTool(BaseTool):
    name = "search_files"
    description = "Search for files matching a pattern or name across a folder."
    category = ToolCategory.FILESYSTEM
    permission = PermissionLevel.SAFE
    parameters_schema = {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Filename or pattern (e.g. *.pdf, project, notes.txt)"},
            "directory": {"type": "string", "description": "Base directory to search in (defaults to user home or current folder)"}
        },
        "required": ["query"]
    }

    def execute(self, query: str, directory: Optional[str] = None, max_results: int = 15, **kwargs) -> ToolResult:
        base_dir = directory or os.path.expanduser("~")
        is_safe, reason = safety_engine.is_path_safe(base_dir)
        if not is_safe:
            return ToolResult(success=False, output=None, error=reason)

        results = []
        try:
            pattern = f"*{query}*" if not ("*" in query or "?" in query) else query
            for root, dirs, files in os.walk(base_dir):
                for file in files:
                    if glob.fnmatch.fnmatch(file.lower(), pattern.lower()):
                        results.append(os.path.join(root, file))
                        if len(results) >= max_results:
                            break
                if len(results) >= max_results:
                    break

            if results:
                return ToolResult(success=True, output=f"Found {len(results)} files:\n" + "\n".join(results), metadata={"files": results})
            return ToolResult(success=True, output=f"No files found matching '{query}' in '{base_dir}'.")
        except Exception as e:
            return ToolResult(success=False, output=None, error=f"File search failed: {str(e)}")

class ReadFileTool(BaseTool):
    name = "read_file"
    description = "Read the content of a text, markdown, or code file."
    category = ToolCategory.FILESYSTEM
    permission = PermissionLevel.SAFE
    parameters_schema = {
        "type": "object",
        "properties": {
            "file_path": {"type": "string", "description": "Path of file to read"}
        },
        "required": ["file_path"]
    }

    def execute(self, file_path: str, max_chars: int = 4000, **kwargs) -> ToolResult:
        is_safe, reason = safety_engine.is_path_safe(file_path)
        if not is_safe:
            return ToolResult(success=False, output=None, error=reason)

        if not os.path.exists(file_path):
            return ToolResult(success=False, output=None, error=f"File not found: {file_path}")

        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read(max_chars)
            return ToolResult(success=True, output=content)
        except Exception as e:
            return ToolResult(success=False, output=None, error=f"Error reading file: {str(e)}")

class DeleteFileTool(BaseTool):
    name = "delete_file"
    description = "Safely delete a file (Requires user confirmation)."
    category = ToolCategory.FILESYSTEM
    permission = PermissionLevel.CONFIRM_REQUIRED
    parameters_schema = {
        "type": "object",
        "properties": {
            "file_path": {"type": "string", "description": "Path of file to delete"}
        },
        "required": ["file_path"]
    }

    def execute(self, file_path: str, **kwargs) -> ToolResult:
        is_safe, reason = safety_engine.is_path_safe(file_path, for_writing=True)
        if not is_safe:
            return ToolResult(success=False, output=None, error=reason)

        if not os.path.exists(file_path):
            return ToolResult(success=False, output=None, error=f"File not found: {file_path}")

        try:
            os.remove(file_path)
            return ToolResult(success=True, output=f"Deleted file: {file_path}")
        except Exception as e:
            return ToolResult(success=False, output=None, error=f"Failed to delete file: {str(e)}")
