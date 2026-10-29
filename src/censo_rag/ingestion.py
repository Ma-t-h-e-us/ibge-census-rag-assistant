"""Rebuild the local corpus from the versioned IBGE source manifest."""

import hashlib
import json
import re
import urllib.request
from pathlib import Path

from pypdf import PdfReader

from .chunking import chunk_words, normalize_text


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def ensure_source(root: Path, source: dict, download: bool) -> Path:
    path = root / source["local_path"]
    if not path.exists():
        if not download:
            raise FileNotFoundError(f"Missing {path}; run ingestion with --download")
        path.parent.mkdir(parents=True, exist_ok=True)
        request = urllib.request.Request(source["download_url"], headers={"User-Agent": "ibge-census-rag-assistant/0.1"})
        temporary = path.with_suffix(".download")
        try:
            with urllib.request.urlopen(request, timeout=60) as response, temporary.open("wb") as output:
                for block in iter(lambda: response.read(1024 * 1024), b""):
                    output.write(block)
            if sha256_file(temporary) != source["sha256"]:
                raise ValueError(f"Downloaded file differs from manifest: {source['id']}")
            temporary.replace(path)
        finally:
            temporary.unlink(missing_ok=True)
    actual = sha256_file(path)
    if actual != source["sha256"]:
        raise ValueError(f"SHA-256 mismatch for {path}: expected {source['sha256']}, got {actual}")
    return path


def selected_text(source: dict, pdf_page: int, text: str) -> str:
    """Apply the two reviewed section boundaries before normalizing whitespace."""
    if source["id"] == "ibge-censo2022-primeiros-resultados":
        text = re.sub(r"^\s*\d+\s*\n", "", text, count=1)
        if pdf_page == 11:
            match = re.search(r"(?m)^Notas técnicas\s*$", text)
            if not match:
                raise ValueError("Start marker 'Notas técnicas' missing on PDF page 11")
            text = text[match.start() :]
        if pdf_page == 19:
            match = re.search(r"(?m)^Tratamento dos dados\s*$", text)
            if not match:
                raise ValueError("End marker 'Tratamento dos dados' missing on PDF page 19")
            text = text[: match.start()]
    else:
        # The note repeats its title and page number in the PDF header.
        text = re.sub(r"(?s)^.*?Nota metodológica n\. 01\s*\d+\s*", "", text, count=1)
    return normalize_text(text)


def build_corpus(root: Path, download: bool = False, max_words: int = 180, overlap_words: int = 35) -> dict:
    manifest_path = root / "data" / "source_manifest.json"
    manifest_bytes = manifest_path.read_bytes()
    manifest = json.loads(manifest_bytes)
    output_dir = root / "data" / "processed"
    chunks = []
    page_counts = {}

    for source in manifest["sources"]:
        pdf = PdfReader(ensure_source(root, source, download))
        if len(pdf.pages) != source["total_pdf_pages"]:
            raise ValueError(f"Page count changed for {source['id']}")
        first = source["selected_pdf_pages"]["start"]
        last = source["selected_pdf_pages"]["end"]
        for page_number in range(first, last + 1):
            text = selected_text(source, page_number, pdf.pages[page_number - 1].extract_text() or "")
            if len(text) < 100:
                raise ValueError(f"Too little extracted text: {source['id']} page {page_number}")
            page_counts[f"{source['id']}:{page_number}"] = len(text)
            for ordinal, chunk in enumerate(chunk_words(text, max_words, overlap_words), start=1):
                fingerprint = hashlib.sha256(chunk.encode("utf-8")).hexdigest()[:12]
                chunks.append({
                    "id": f"{source['id']}:p{page_number}:c{ordinal}:{fingerprint}",
                    "source_id": source["id"],
                    "source_title": source["title"],
                    "source_url": source["source_url"],
                    "pdf_page": page_number,
                    "printed_page": page_number + source["printed_page_offset"],
                    "text": chunk,
                })

    if not chunks:
        raise ValueError("No chunks generated")
    output_dir.mkdir(parents=True, exist_ok=True)
    chunks_path = output_dir / "chunks.jsonl"
    content = "".join(json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n" for item in chunks)
    chunks_path.write_text(content, encoding="utf-8", newline="\n")
    report = {
        "manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
        "chunks_sha256": hashlib.sha256(content.encode("utf-8")).hexdigest(),
        "source_count": len(manifest["sources"]),
        "page_count": len(page_counts),
        "chunk_count": len(chunks),
        "max_words": max_words,
        "overlap_words": overlap_words,
        "characters_by_page": page_counts,
    }
    (output_dir / "build_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report
