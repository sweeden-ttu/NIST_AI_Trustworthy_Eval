"""Load homework text from a path (PDF companion .txt or plain text)."""

from pathlib import Path


def load_homework_excerpt(homework_pdf: str | None, max_chars: int = 16000) -> str:
    """Return excerpt for LLM prompts.

    - If path is None, returns a placeholder.
    - If a same-stem ``.txt`` exists next to a ``.pdf``, reads that (no PDF parser required).
    - If path is ``.txt``, reads it.
    - Otherwise returns the path string and a hint to add a sidecar ``.txt``.
    """
    if not homework_pdf:
        return "Not provided"

    p = Path(homework_pdf).expanduser()
    if not p.exists():
        return f"(path not found: {homework_pdf})"

    if p.suffix.lower() == ".txt":
        return p.read_text(encoding="utf-8", errors="replace")[:max_chars]

    if p.suffix.lower() == ".pdf":
        sidecar = p.with_suffix(".txt")
        if sidecar.is_file():
            return sidecar.read_text(encoding="utf-8", errors="replace")[:max_chars]
        try:
            from pypdf import PdfReader  # type: ignore[import-untyped]

            reader = PdfReader(str(p))
            parts: list[str] = []
            for page in reader.pages:
                t = page.extract_text() or ""
                parts.append(t)
                if sum(len(x) for x in parts) >= max_chars:
                    break
            return "\n".join(parts)[:max_chars]
        except ImportError:
            return (
                f"(PDF at {p}; install optional dependency 'pypdf' or add {sidecar.name} with extracted text)"
            )

    return p.read_text(encoding="utf-8", errors="replace")[:max_chars]
