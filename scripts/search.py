"""Inspect the evidence retrieved for one question."""

import argparse
import sys
from pathlib import Path

from censo_rag.retrieval import LexicalRetriever, SemanticRetriever, load_chunks


def main() -> None:
    parser = argparse.ArgumentParser(description="Search the selected IBGE Census documents")
    parser.add_argument("question", help="Question in Portuguese")
    parser.add_argument("--method", choices=("lexical", "semantic"), default="lexical")
    parser.add_argument("--top-k", type=int, default=5)
    args = parser.parse_args()
    if args.top_k < 1:
        parser.error("--top-k must be positive")

    root = Path(__file__).resolve().parents[1]
    chunks = load_chunks(root / "data" / "processed" / "chunks.jsonl")
    if args.method == "lexical":
        retriever = LexicalRetriever(chunks)
    else:
        retriever = SemanticRetriever(chunks, root / "data" / "models")
    hits = retriever.search(args.question, args.top_k)
    if not hits:
        print("Nenhum trecho encontrado para os termos da pergunta.")
        return
    for rank, hit in enumerate(hits, start=1):
        chunk = hit.chunk
        print(f"\n{rank}. {chunk['source_title']} — página impressa {chunk['printed_page']} (PDF {chunk['pdf_page']})")
        print(f"   Pontuação: {hit.score:.4f} | Trecho: {chunk['id']}")
        print(f"   Fonte: {chunk['source_url']}#page={chunk['pdf_page']}")
        print(f"   Texto: {chunk['text'][:700]}{'…' if len(chunk['text']) > 700 else ''}")


if __name__ == "__main__":
    try:
        main()
    except (FileNotFoundError, RuntimeError, ValueError) as exc:
        sys.exit(str(exc))
