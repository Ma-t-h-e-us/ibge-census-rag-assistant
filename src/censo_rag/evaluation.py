"""Evaluate retrieved evidence pages without using reference answers at search time."""

import statistics
import time


def score_pages(expected: set[tuple[str, int]], results: list, k: int) -> dict:
    found = {(hit.chunk["source_id"], hit.chunk["pdf_page"]) for hit in results[:k]}
    matched = expected & found
    return {
        "any_page_hit": bool(matched),
        "all_pages_hit": expected <= found,
        "page_recall": len(matched) / len(expected),
    }


def _percentile(values: list[float], percent: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    position = (len(ordered) - 1) * percent / 100
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def evaluate(retriever, questions: list[dict], k_values: tuple[int, ...] = (1, 3, 5)) -> dict:
    if not k_values or min(k_values) < 1:
        raise ValueError("k_values must contain positive integers")
    max_k = max(k_values)
    rows = []
    # Warm up each method so timing does not include first-use library initialization.
    retriever.search("Censo Demográfico 2022", max_k)
    for item in questions:
        start = time.perf_counter()
        hits = retriever.search(item["question"], max_k)
        elapsed_ms = (time.perf_counter() - start) * 1000
        row = {
            "id": item["id"],
            "split": item["split"],
            "category": item["category"],
            "expected_behavior": item["expected_behavior"],
            "retrieval_ms": round(elapsed_ms, 3),
            "top_results": [
                {
                    "chunk_id": hit.chunk["id"],
                    "source_id": hit.chunk["source_id"],
                    "pdf_page": hit.chunk["pdf_page"],
                    "score": round(hit.score, 5),
                }
                for hit in hits
            ],
        }
        if item["expected_behavior"] == "answer":
            expected = {(page["source_id"], page["pdf_page"]) for page in item["evidence"]}
            if not expected:
                raise ValueError(f"Answer question {item['id']} has no evidence pages")
            row["evidence_metrics"] = {str(k): score_pages(expected, hits, k) for k in k_values}
        rows.append(row)

    by_split = {}
    for split in sorted({row["split"] for row in rows}):
        subset = [row for row in rows if row["split"] == split]
        answers = [row for row in subset if row["expected_behavior"] == "answer"]
        if not answers:
            raise ValueError(f"No answer questions in split {split}")
        times = [row["retrieval_ms"] for row in subset]
        by_split[split] = {
            "questions": len(subset),
            "answer_questions": len(answers),
            "unscored_non_answer_questions": len(subset) - len(answers),
            "any_page_hit_at_k": {
                str(k): round(statistics.mean(row["evidence_metrics"][str(k)]["any_page_hit"] for row in answers), 4)
                for k in k_values
            },
            "all_pages_hit_at_k": {
                str(k): round(statistics.mean(row["evidence_metrics"][str(k)]["all_pages_hit"] for row in answers), 4)
                for k in k_values
            },
            "mean_page_recall_at_k": {
                str(k): round(statistics.mean(row["evidence_metrics"][str(k)]["page_recall"] for row in answers), 4)
                for k in k_values
            },
            "retrieval_latency_ms": {
                "median": round(statistics.median(times), 3),
                "p95": round(_percentile(times, 95), 3),
            },
        }
    return {"splits": by_split, "questions": rows}
