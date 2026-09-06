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

SENSITIVE = re.compile(
    r"(?:cookie|authorization|bearer|token|csrf|password|passwd|secret|"
    r"mfa|session|account.?number|id.?number|identity|email|phone)", re.I)


class SensitiveCaptureError(ValueError):
    """Raised when a capture still contains data that must not be ingested."""


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
