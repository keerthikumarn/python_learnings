"""
pdf_service.py — Service layer for PDF processing.

Responsibility: Extract and validate text content from uploaded PDF files.
Analogous to a @Service bean in Spring Boot.
"""

import tempfile
import os
import pymupdf4llm

from configuration import MAX_PAPER_CHARS, WARNING_PAPER_CHARS


class PdfProcessingResult:
    """
    Value object encapsulating the outcome of a PDF processing attempt.
    Analogous to a DTO / Result<T> pattern in Java.
    """

    def __init__(self, text: str = None, error: str = None, warning: str = None):
        self.text = text
        self.error = error
        self.warning = warning

    @property
    def is_success(self) -> bool:
        return self.text is not None and self.error is None


def extract_text_from_pdf(uploaded_file) -> PdfProcessingResult:
    tmp_file_path = None
    try:
        tmp_file_path = _write_to_temp_file(uploaded_file)
        document_text = pymupdf4llm.to_markdown(tmp_file_path)
        return _validate_document_size(document_text)
    except Exception as e:
        return PdfProcessingResult(error=f"Error processing PDF: {str(e)}")
    finally:
        _cleanup_temp_file(tmp_file_path)


# ── Private helpers ──────────────────────────────────────────────────────────

def _write_to_temp_file(uploaded_file) -> str:
    """Writes the uploaded file bytes to a named temporary file and returns its path."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        tmp_file.write(uploaded_file.getvalue())
        return tmp_file.name


def _validate_document_size(document_text: str) -> PdfProcessingResult:
    """
    Enforces character-count limits on extracted text.
    Returns an error result if the document exceeds MAX_PAPER_CHARS,
    or a warning result if it exceeds WARNING_PAPER_CHARS.
    """
    length = len(document_text)

    if length > MAX_PAPER_CHARS:
        return PdfProcessingResult(
            error=(
                f"Paper is too large ({length:,} characters). "
                f"Maximum supported size is {MAX_PAPER_CHARS:,} characters. "
                "Please upload a shorter paper or split it into sections."
            )
        )

    warning = None
    if length > WARNING_PAPER_CHARS:
        warning = (
            f"Paper is quite large ({length:,} characters). "
            "This may result in higher API costs and slower responses."
        )

    return PdfProcessingResult(text=document_text, warning=warning)


def _cleanup_temp_file(path: str) -> None:
    """Silently removes a temporary file if it still exists."""
    if path and os.path.exists(path):
        try:
            os.unlink(path)
        except Exception:
            pass  # Non-fatal; OS will reclaim on process exit