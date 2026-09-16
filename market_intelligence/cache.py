"""Deterministic cache keys for document extraction and provider analysis."""
from __future__ import annotations
import hashlib
import json

def cache_key(content_hash: str, *, provider: str, model: str, schema_version: str, prompt_version: str) -> str:
    payload=json.dumps([content_hash,provider,model,schema_version,prompt_version], separators=(",",":"))
    return hashlib.sha256(payload.encode()).hexdigest()

class AnalysisCache:
    def __init__(self): self._items={}
    def get(self, key): return self._items.get(key)
    def put(self, key, value): self._items[key]=value; return value
