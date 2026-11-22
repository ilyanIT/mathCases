"""Extract text from text-based PDFs with PyMuPDF (no OCR)."""
from __future__ import annotations

import pymupdf

# Fewer characters than this usually means a scanned/image-only PDF.
MIN_TEXT_CHARS = 50


class PdfExtractError(Exception):
    """Raised with a founder-friendly message when a PDF can't be read."""


def extract_text(pdf_bytes: bytes) -> str:
    """Return the PDF's text, page by page. Raises PdfExtractError."""
    try:
        doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
    except Exception as exc:
        raise PdfExtractError("This file doesn't look like a valid PDF.") from exc

    with doc:
        if doc.needs_pass:
            raise PdfExtractError("This PDF is password-protected.")
        pages = [page.get_text("text") for page in doc]

    text = "\n\n".join(p.strip() for p in pages if p.strip())
    if len(text) < MIN_TEXT_CHARS:
        raise PdfExtractError(
            "We couldn't find any text in this PDF. It may be a scanned image."
        )
    return text
