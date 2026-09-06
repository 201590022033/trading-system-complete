"""Safe structural evidence handling for user-supplied ViewPoint exports.

This module deliberately does not parse broker values or infer endpoints. It
accepts an already-sanitized HAR-like JSON document and returns field/method/
content-type evidence only.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

SENSITIVE = re.compile(
    r"(?:cookie|authorization|bearer|token|csrf|password|passwd|secret|"
    r"mfa|session|account.?number|id.?number|identity|email|phone)", re.I)


class SensitiveCaptureError(ValueError):
    """Raised when a capture still contains data that must not be ingested."""


def _field_names(value: Any, prefix: str = "") -> set[str]:
    names: set[str] = set()
    if isinstance(value, dict):
        for key, item in value.items():
            key = str(key)
            if not SENSITIVE.search(key):
                names.add(f"{prefix}.{key}" if prefix else key)
                names |= _field_names(item, f"{prefix}.{key}" if prefix else key)
    elif isinstance(value, list):
        for item in value[:20]:
            names |= _field_names(item, prefix)
    return names


def sanitize_har_file(input_path: str | Path, output_path: str | Path) -> dict[str, Any]:
    """Convert a raw HAR to structural evidence without retaining values."""
    raw = json.loads(Path(input_path).read_text(encoding="utf-8"))
    entries = raw.get("log", {}).get("entries", [])
    if not isinstance(entries, list):
        raise ValueError("HAR log.entries must be a list")
    structural = []
    for item in entries:
        request = item.get("request", {})
        response = item.get("response", {})
        url = str(request.get("url", ""))
        parts = urlsplit(url)
        path = parts.path or "/"
        response_content = response.get("content", {})
        fields = _field_names(response_content.get("_json", {}))
        # Some HAR producers store JSON as text; parse it transiently only.
        text_value = response_content.get("text")
        if not fields and isinstance(text_value, str) and "json" in str(response_content.get("mimeType", "")):
            try:
                fields = _field_names(json.loads(text_value))
            except (ValueError, TypeError):
                pass
        resource = str(item.get("_resourceType", "")).lower()
        transport = "websocket" if resource == "websocket" or "websocket" in path.lower() else (
            "fetch" if resource in {"fetch", "xhr"} else "http")
        structural.append({"method": str(request.get("method", "UNKNOWN")),
            "path": path, "content_type": str(response_content.get("mimeType", "UNKNOWN")).split(";", 1)[0],
            "transport": transport, "field_names": sorted(fields)})
    result = {"sanitized": True, "source": "HAR structural extraction",
              "entries": structural, "entry_count": len(structural)}
    checked = ingest_sanitized_capture(result)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_path).write_text(json.dumps(checked, indent=2, sort_keys=True), encoding="utf-8")
    return checked


def _check(value: Any, path: str = "root") -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if SENSITIVE.search(str(key)):
                raise SensitiveCaptureError(f"sensitive field remains at {path}.{key}")
            _check(item, f"{path}.{key}")
    elif isinstance(value, list):
        for i, item in enumerate(value):
            _check(item, f"{path}[{i}]")
    elif isinstance(value, str) and SENSITIVE.search(value):
        raise SensitiveCaptureError(f"sensitive marker remains at {path}")


def ingest_sanitized_capture(document: dict[str, Any]) -> dict[str, Any]:
    """Return a minimal structural summary, or fail closed.

    Expected input is intentionally generic: ``entries`` may contain method,
    path, content_type, transport and field_names. No ViewPoint schema is
    assumed and no values are retained.
    """
    if not isinstance(document, dict) or document.get("sanitized") is not True:
        raise SensitiveCaptureError("capture must explicitly be marked sanitized")
    _check(document)
    entries = document.get("entries", [])
    if not isinstance(entries, list):
        raise ValueError("entries must be a list")
    summary = []
    for entry in entries:
        if not isinstance(entry, dict):
            raise ValueError("each entry must be an object")
        summary.append({
            "method": entry.get("method", "UNKNOWN"),
            "path": entry.get("path", "UNKNOWN"),
            "content_type": entry.get("content_type", "UNKNOWN"),
            "transport": entry.get("transport", "UNKNOWN"),
            "field_names": sorted(set(entry.get("field_names", []))),
            "message_type": entry.get("message_type"),
        })
    return {"sanitized": True, "entries": summary, "entry_count": len(summary)}


def ingest_sanitized_file(path: str | Path) -> dict[str, Any]:
    return ingest_sanitized_capture(json.loads(Path(path).read_text(encoding="utf-8")))
