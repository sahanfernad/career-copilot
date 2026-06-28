"""
Part 1 — Document Reader
-------------------------
Deterministic, non-LLM preprocessing step: turns a resume file (PDF, DOCX,
or plain text) into a plain text string the Resume & Job-Match Agent can
read. This stays outside the agent on purpose — file parsing is a solved,
deterministic problem and doesn't need a model call. The LLM agent's job
starts only once we already have clean text.

In Part 4, this gets wrapped behind an MCP server so it's exposed as a
tool over the Model Context Protocol (this satisfies the "MCP Server"
course concept). For now it's called directly as a plain Python function.
"""

from pathlib import Path

import pypdf
from docx import Document


def read_resume(file_path: str) -> str:
    """Read a resume file and return its plain text content.

    Supports .pdf, .docx, and .txt. Raises ValueError for unsupported
    formats, and FileNotFoundError if the path doesn't exist.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Resume file not found: {file_path}")

    suffix = path.suffix.lower()

    if suffix == ".pdf":
        return _read_pdf(path)
    elif suffix == ".docx":
        return _read_docx(path)
    elif suffix == ".txt":
        return path.read_text(encoding="utf-8")
    else:
        raise ValueError(
            f"Unsupported resume format: {suffix}. Use .pdf, .docx, or .txt"
        )


def _read_pdf(path: Path) -> str:
    reader = pypdf.PdfReader(str(path))
    pages = [page.extract_text() or "" for page in reader.pages]
    text = "\n".join(pages).strip()
    if not text:
        raise ValueError(
            "No extractable text found in PDF. If this is a scanned/image "
            "resume, it's out of scope for this project (we deliberately "
            "cut scanned-image parsing — see blueprint scope table)."
        )
    return text


def _read_docx(path: Path) -> str:
    doc = Document(str(path))
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    return "\n".join(paragraphs)


def read_job_description(jd_text_or_path: str) -> str:
    """JD is usually pasted text, but allow a file path too, for flexibility."""
    candidate_path = Path(jd_text_or_path)
    if candidate_path.exists() and candidate_path.suffix.lower() == ".txt":
        return candidate_path.read_text(encoding="utf-8")
    return jd_text_or_path.strip()


if __name__ == "__main__":
    # Quick manual smoke test — run: python utils/document_reader.py
    import sys

    if len(sys.argv) > 1:
        print(read_resume(sys.argv[1])[:500])
    else:
        print("Usage: python utils/document_reader.py path/to/resume.pdf")
