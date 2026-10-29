"""CLI entry point for rebuilding the local corpus."""

import argparse
import json
from pathlib import Path

from censo_rag.ingestion import build_corpus


def main() -> None:
    parser = argparse.ArgumentParser(description="Build page-cited chunks from IBGE PDFs")
    parser.add_argument("--download", action="store_true", help="Download missing PDFs and verify their hashes")
    parser.add_argument("--max-words", type=int, default=180)
    parser.add_argument("--overlap-words", type=int, default=35)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    report = build_corpus(root, args.download, args.max_words, args.overlap_words)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
