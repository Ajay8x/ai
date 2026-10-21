"""
AJAX AI - Automatic JSON-to-Schema Field Mapper & Form Builder
Supports 14 data types:
Text, Textarea, Number, Boolean, Date, DateTime, Email, URL, Select, Multi-select, Array, Object, GeoPoint, Image URL.
Safe JSONPath extraction, type inference, key deduplication, depth limits, and preview generator.
"""

import re
import json
import datetime
from typing import Dict, Any, List, Optional, Tuple, Union
from connectors.base import FieldType, SchemaField
from connectors.loop_detector import loop_manager

EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')
URL_REGEX = re.compile(r'^https?://[^\s/$.?#].[^\s]*$', re.IGNORECASE)
IMAGE_EXT_REGEX = re.compile(r'\.(jpg|jpeg|png|webp|gif|svg)(\?.*)?$', re.IGNORECASE)
DATE_REGEX = re.compile(r'^\d{4}-\d{2}-\d{2}$')
DATETIME_REGEX = re.compile(r'^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}')

class JSONSchemaMapper:
    """Infers form schemas and field types from arbitrary JSON payloads safely."""

    def __init__(self, max_depth: int = 6, max_array_samples: int = 25):
        self.max_depth = max_depth
        self.max_array_samples = max_array_samples

    def infer_type(self, val: Any) -> FieldType:
        """Determines best-fitting FieldType for a given Python/JSON value."""
        if val is None:
            return FieldType.TEXT
        if isinstance(val, bool):
            return FieldType.BOOLEAN
        if isinstance(val, (int, float)):
            return FieldType.NUMBER
        if isinstance(val, list):
            return FieldType.ARRAY
        if isinstance(val, dict):
            # Check GeoPoint: {lat, lon} or {latitude, longitude}
            keys = {k.lower() for k in val.keys()}
            if ({"lat", "lon"}.issubset(keys) or {"latitude", "longitude"}.issubset(keys)) and len(keys) <= 4:
                return FieldType.GEO_POINT
            return FieldType.OBJECT
        if isinstance(val, str):
            s = val.strip()
            if not s:
                return FieldType.TEXT
            if EMAIL_REGEX.match(s):
                return FieldType.EMAIL
            if URL_REGEX.match(s):
                if IMAGE_EXT_REGEX.search(s) or "image" in s.lower() or "avatar" in s.lower() or "photo" in s.lower():
                    return FieldType.IMAGE_URL
                return FieldType.URL
            if DATETIME_REGEX.match(s):
                return FieldType.DATETIME
            if DATE_REGEX.match(s):
                return FieldType.DATE
            if len(s) > 120 or "\n" in s:
                return FieldType.TEXTAREA
            return FieldType.TEXT
        return FieldType.TEXT

    def to_readable_label(self, key: str) -> str:
        """Converts camelCase, snake_case or dotted keys into clean Title Case labels."""
        clean = key.split(".")[-1]
        clean = clean.replace("_", " ").replace("-", " ")
        # Convert camelCase to spaces
        clean = re.sub(r'([a-z])([A-Z])', r'\1 \2', clean)
        return clean.strip().title()

    def generate_stable_key(self, path: str, existing_keys: List[str]) -> str:
        """Generates a stable, collision-free identifier key."""
        base = path.lower().replace(".", "_").replace("[", "_").replace("]", "").replace("-", "_")
        base = re.sub(r'[^a-z0-9_]', '', base).strip("_")
        if not base:
            base = "field"

        candidate = base
        counter = 1
        while candidate in existing_keys:
            candidate = f"{base}_{counter}"
            counter += 1
        return candidate

    def extract_by_jsonpath(self, data: Any, json_path: str) -> Any:
        """Safe dot-notation / array-index JSONPath accessor without external dependencies."""
        if not json_path or json_path in ("$", "@", "root"):
            return data

        parts = json_path.lstrip("$. ").split(".")
        curr = data
        for part in parts:
            if curr is None:
                return None
            # Check array index notation e.g. items[0]
            arr_match = re.match(r'^(\w+)\[(\d+)\]$', part)
            if arr_match:
                name, idx = arr_match.groups()
                if isinstance(curr, dict) and name in curr:
                    curr = curr[name]
                    if isinstance(curr, list) and int(idx) < len(curr):
                        curr = curr[int(idx)]
                    else:
                        return None
                else:
                    return None
            elif isinstance(curr, dict):
                curr = curr.get(part)
            else:
                return None
        return curr

    def infer_schema(self, json_payload: Any, data_path: str = "") -> List[SchemaField]:
        """
        Recursively extracts schema fields from JSON payload with loop & depth protection.
        """
        # Validate circular structures and depth
        loop_manager.schema_guard.validate_nesting(json_payload)

        target_data = self.extract_by_jsonpath(json_payload, data_path) if data_path else json_payload
        if target_data is None:
            return []

        # If array at root/target, sample first item
        if isinstance(target_data, list):
            if not target_data:
                return []
            target_data = target_data[0]

        fields: List[SchemaField] = []
        existing_keys: List[str] = []

        self._walk_and_collect(target_data, prefix="", json_path_prefix="$", fields=fields, existing_keys=existing_keys, depth=0)
        return fields

    def _walk_and_collect(
        self,
        node: Any,
        prefix: str,
        json_path_prefix: str,
        fields: List[SchemaField],
        existing_keys: List[str],
        depth: int
    ) -> None:
        if depth > self.max_depth or len(fields) >= loop_manager.schema_guard.max_fields:
            return

        if isinstance(node, dict):
            # Check if this node itself is a GeoPoint
            inferred = self.infer_type(node)
            if inferred == FieldType.GEO_POINT and prefix:
                key = self.generate_stable_key(prefix, existing_keys)
                existing_keys.append(key)
                fields.append(SchemaField(
                    key=key,
                    label=self.to_readable_label(prefix),
                    field_type=FieldType.GEO_POINT,
                    json_path=json_path_prefix,
                    sample_value=node
                ))
                return

            for k, v in node.items():
                child_path = f"{prefix}.{k}" if prefix else k
                child_jsonpath = f"{json_path_prefix}.{k}"

                child_type = self.infer_type(v)
                if child_type == FieldType.OBJECT:
                    # Recurse into object
                    self._walk_and_collect(v, child_path, child_jsonpath, fields, existing_keys, depth + 1)
                elif child_type == FieldType.ARRAY:
                    # Check list elements
                    key = self.generate_stable_key(child_path, existing_keys)
                    existing_keys.append(key)
                    sample = v[:3] if isinstance(v, list) else v
                    fields.append(SchemaField(
                        key=key,
                        label=self.to_readable_label(k),
                        field_type=FieldType.ARRAY,
                        json_path=child_jsonpath,
                        sample_value=sample
                    ))
                else:
                    key = self.generate_stable_key(child_path, existing_keys)
                    existing_keys.append(key)
                    fields.append(SchemaField(
                        key=key,
                        label=self.to_readable_label(k),
                        field_type=child_type,
                        json_path=child_jsonpath,
                        sample_value=v
                    ))

    def generate_form_preview(self, fields: List[SchemaField], sample_json: Any) -> Dict[str, Any]:
        """Generates dynamic form field previews mapped with actual sample data."""
        preview_data = {}
        for f in fields:
            extracted = self.extract_by_jsonpath(sample_json, f.json_path)
            preview_data[f.key] = {
                "label": f.label,
                "type": f.field_type.value,
                "json_path": f.json_path,
                "value": extracted if extracted is not None else f.default_value,
                "required": f.required
            }
        return preview_data

schema_mapper = JSONSchemaMapper()
