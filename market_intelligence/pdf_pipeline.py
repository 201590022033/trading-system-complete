"""Bounded, offline-friendly PDF/document processing primitives."""
from __future__ import annotations
import hashlib
import io
import re
from dataclasses import dataclass
from urllib.parse import urlsplit

MAX_DOCUMENT_BYTES = 10 * 1024 * 1024
PDF_MAGIC = b"%PDF-"

@dataclass(frozen=True)
class DocumentPayload:
    content: bytes
    content_hash: str
    mime_type: str
    extraction_method: str
    text: str

def validate_document(content: bytes, *, content_type: str = "application/pdf", max_bytes: int = MAX_DOCUMENT_BYTES) -> None:
    if not isinstance(content, bytes) or not content:
        raise ValueError("document is empty")
    if len(content) > max_bytes:
        raise ValueError("document exceeds configured size limit")
    if not content.startswith(PDF_MAGIC):
        raise ValueError("document signature is not PDF")
    if "pdf" not in (content_type or "").lower():
        raise ValueError("document MIME type is not PDF")

def content_hash(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()

def extract_text(content: bytes) -> tuple[str, str]:
    validate_document(content)
    try:
        from pypdf import PdfReader
        text = "\n".join(page.extract_text() or "" for page in PdfReader(io.BytesIO(content)).pages).strip()
        if text:
            return re.sub(r"\s+", " ", text), "embedded_text"
    except Exception:
        pass
    # OCR is intentionally not automatic: callers must supply an approved OCR implementation.
    return "", "unavailable_embedded_text"

def process_pdf(content: bytes, *, content_type: str = "application/pdf", max_bytes: int = MAX_DOCUMENT_BYTES) -> DocumentPayload:
    validate_document(content, content_type=content_type, max_bytes=max_bytes)
    text, method = extract_text(content)
    return DocumentPayload(content, content_hash(content), content_type, method, text)

def validate_url(url: str, allowed_hosts: set[str]) -> str:
    parsed = urlsplit(url)
    if parsed.scheme != "https" or parsed.hostname not in allowed_hosts or parsed.username or parsed.password:
        raise ValueError("URL is outside the permitted HTTPS host policy")
    return url
