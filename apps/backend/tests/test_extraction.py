import pytest

from app.core.errors import AppError
from app.services.extraction import extract_document


def test_extracts_utf8_text() -> None:
    result = extract_document(
        filename="synthetic.txt",
        content_type="text/plain",
        data=b"Synthetic report with enough text for safe extraction.",
        max_bytes=1024,
    )
    assert result.filename == "synthetic.txt"
    assert "Synthetic report" in result.text


def test_rejects_unsupported_extension() -> None:
    with pytest.raises(AppError, match="Unsupported"):
        extract_document(filename="payload.exe", content_type=None, data=b"content", max_bytes=1024)


def test_rejects_oversized_file() -> None:
    with pytest.raises(AppError) as error:
        extract_document(filename="x.txt", content_type="text/plain", data=b"x" * 50, max_bytes=10)
    assert error.value.status_code == 413

