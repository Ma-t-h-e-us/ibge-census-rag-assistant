"""Compare lexical and semantic evidence retrieval on the fixed question set."""

import argparse
import importlib.metadata
import json
import sys
import time
from pathlib import Path

from censo_rag.evaluation import evaluate
from censo_rag.retrieval import SEMANTIC_MODEL, SEMANTIC_MODEL_REVISION, SEMANTIC_VECTOR_FORMAT, LexicalRetriever, SemanticRetriever, chunks_sha256, load_chunks


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate page retrieval on the IBGE question set")
    parser.add_argument("--method", choices=("lexical", "semantic", "both"), default="both")
    parser.add_argument("--output", type=Path, help="JSON report path; default eval/results/retrieval_report.json")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    chunks = load_chunks(root / "data" / "processed" / "chunks.jsonl")
    questions = [json.loads(line) for line in (root / "eval" / "questions.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    methods = ("lexical", "semantic") if args.method == "both" else (args.method,)
    results = {}
    for method in methods:
        start = time.perf_counter()
        if method == "lexical":
            retriever = LexicalRetriever(chunks)
        else:
            retriever = SemanticRetriever(chunks, root / "data" / "models")
        build_ms = round((time.perf_counter() - start) * 1000, 3)
        results[method] = {
            "index_build_or_load_ms": build_ms,
            "vector_cache_hit": retriever.cache_hit if method == "semantic" else None,
            **evaluate(retriever, questions),
        }
        print(f"{method}: índice pronto em {build_ms:.1f} ms")
        for split, summary in results[method]["splits"].items():
            print(f"  {split}: página correta no top 5 = {summary['any_page_hit_at_k']['5']:.1%}; "
                  f"todas as páginas = {summary['all_pages_hit_at_k']['5']:.1%}")

    report = {
        "corpus_sha256": chunks_sha256(chunks),
        "chunk_count": len(chunks),
        "question_count": len(questions),
        "metric_unit": "distinct (source_id, pdf_page) pairs; only expected_behavior=answer is scored",
        "evaluation_note": "Exploratory comparison: the test split was visible during embedding-model selection; use a new holdout for a final generalization estimate.",
        "semantic_model": SEMANTIC_MODEL if "semantic" in methods else None,
        "semantic_model_revision": SEMANTIC_MODEL_REVISION if "semantic" in methods else None,
        "semantic_vector_format": SEMANTIC_VECTOR_FORMAT if "semantic" in methods else None,
        "versions": {
            "scikit-learn": importlib.metadata.version("scikit-learn"),
            "fastembed": importlib.metadata.version("fastembed") if "semantic" in methods else None,
        },
        "methods": results,
    }
    output = args.output or root / "eval" / "results" / "retrieval_report.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Relatório: {output}")


if __name__ == "__main__":
    try:
        main()
    except (FileNotFoundError, RuntimeError, ValueError) as exc:
        sys.exit(str(exc))
