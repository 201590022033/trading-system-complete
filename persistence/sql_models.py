"""Deterministic serialization helpers for portable repository rows."""

import json
from typing import Any


def dumps(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def loads(value: str | None, default: Any) -> Any:
    return default if value in (None, "") else json.loads(value)
