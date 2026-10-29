"""Deterministic, page-bounded text chunks."""

import re


def normalize_text(text: str) -> str:
    """Remove PDF line-wrap noise without rewriting facts or numbers."""
    text = text.replace("\u00ad", "")
    text = re.sub(r"(?<=\w)-\s*\n\s*(?=\w)", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def chunk_words(text: str, max_words: int = 180, overlap_words: int = 35) -> list[str]:
    if max_words <= 0 or not 0 <= overlap_words < max_words:
        raise ValueError("Require max_words > 0 and 0 <= overlap_words < max_words")
    words = text.split()
    if not words:
        return []
    step = max_words - overlap_words
    chunks = []
    for start in range(0, len(words), step):
        chunk = words[start : start + max_words]
        if not chunk:
            break
        chunks.append(" ".join(chunk))
        if start + max_words >= len(words):
            break
    return chunks
