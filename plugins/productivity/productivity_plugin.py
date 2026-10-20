"""
AJAX AI - Productivity Suite Plugin
"""

import os
from datetime import datetime
from typing import List
from plugins.base import BasePlugin
from tools.base import BaseTool, ToolResult
from core.permissions import PermissionLevel, ToolCategory

from database.db import is_mongo_active, get_mongo_db

NOTES_FILE = os.path.join("data", "quick_notes.txt")

class QuickNoteTool(BaseTool):
    name = "save_quick_note"
    description = "Append a fast scratchpad note with automatic timestamp."
    category = ToolCategory.CUSTOM
    permission = PermissionLevel.SAFE
    parameters_schema = {
        "type": "object",
        "properties": {
            "note": {"type": "string", "description": "Note content to save"}
        },
        "required": ["note"]
    }

    def execute(self, note: str, **kwargs) -> ToolResult:
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            if is_mongo_active():
                db = get_mongo_db()
                db.quick_notes.insert_one({"timestamp": ts, "note": note.strip()})
                return ToolResult(success=True, output=f"Note saved to MongoDB Atlas at {ts}.")
            
            os.makedirs("data", exist_ok=True)
            with open(NOTES_FILE, "a", encoding="utf-8") as f:
                f.write(f"[{ts}] {note.strip()}\n")
            return ToolResult(success=True, output=f"Note saved successfully at {ts}.")
        except Exception as e:
            return ToolResult(success=False, output=None, error=f"Could not save note: {e}")

class ReadNotesTool(BaseTool):
    name = "read_quick_notes"
    description = "Retrieve all saved scratchpad notes."
    category = ToolCategory.CUSTOM
    permission = PermissionLevel.SAFE
    parameters_schema = {
        "type": "object",
        "properties": {}
    }

    def execute(self, **kwargs) -> ToolResult:
        try:
            if is_mongo_active():
                db = get_mongo_db()
                notes = list(db.quick_notes.find({}, {"_id": 0}).sort("timestamp", -1).limit(20))
                if not notes:
                    return ToolResult(success=True, output="No quick notes found in MongoDB Atlas.")
                formatted = "\n".join(f"[{n.get('timestamp')}] {n.get('note')}" for n in notes)
                return ToolResult(success=True, output=formatted)

            if not os.path.exists(NOTES_FILE):
                return ToolResult(success=True, output="No quick notes found.")
            with open(NOTES_FILE, "r", encoding="utf-8") as f:
                content = f.read().strip()
            return ToolResult(success=True, output=content or "No notes saved yet.")
        except Exception as e:
            return ToolResult(success=False, output=None, error=f"Could not read notes: {e}")

class ProductivityPlugin(BasePlugin):
    def on_load(self) -> bool:
        return True

    def on_unload(self) -> bool:
        return True

    def get_tools(self) -> List[BaseTool]:
        return [QuickNoteTool(), ReadNotesTool()]
