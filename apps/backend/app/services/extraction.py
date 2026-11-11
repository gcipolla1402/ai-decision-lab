from __future__ import annotations

import io
from dataclasses import dataclass
from pathlib import Path

import pymupdf as fitz

from app.core.errors import AppError


ALLOWED_SUFFIXES = {".pdf", ".txt"}
ALLOWED_MIME_TYPES = {"application/pdf", "text/plain", "application/octet-stream"}


@dataclass(frozen=True, slots=True)
class ExtractedDocument:
    filename: str
    text: str
    byte_size: int


def extract_document(
    *, filename: str, content_type: str | None, data: bytes, max_bytes: int
) -> ExtractedDocument:
    safe_name = Path(filename or "document").name
    suffix = Path(safe_name).suffix.lower()
    if suffix not in ALLOWED_SUFFIXES:
        raise AppError("Unsupported file type. Upload a PDF or TXT document.")
    if content_type and content_type.lower() not in ALLOWED_MIME_TYPES:
        raise AppError("The file content type is not allowed.")
    if not data:
        raise AppError("The uploaded file is empty.")
    if len(data) > max_bytes:
        raise AppError("The uploaded file exceeds the configured size limit.", status_code=413)

    try:
        text = _extract_pdf(data) if suffix == ".pdf" else _extract_txt(data)
    except (ValueError, UnicodeError, fitz.FileDataError) as exc:
        raise AppError("The document could not be read safely.") from exc

    normalized = "\n".join(line.strip() for line in text.splitlines() if line.strip())
    if len(normalized) < 20:
        raise AppError("The document does not contain enough extractable text.")
    return ExtractedDocument(safe_name, normalized[:60_000], len(data))


def _extract_pdf(data: bytes) -> str:
    with fitz.open(stream=io.BytesIO(data), filetype="pdf") as document:
        if document.page_count > 100:
            raise ValueError("too many pages")
        return "\n".join(page.get_text("text") for page in document)


def _extract_txt(data: bytes) -> str:
    if b"\x00" in data:
        raise ValueError("binary content")
    return data.decode("utf-8-sig")

