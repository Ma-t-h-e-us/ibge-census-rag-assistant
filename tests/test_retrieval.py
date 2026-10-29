import unittest

from censo_rag.evaluation import evaluate, score_pages
from censo_rag.retrieval import LexicalRetriever, SearchResult, chunks_sha256


def chunk(id: str, text: str, page: int) -> dict:
    return {
        "id": id,
        "text": text,
        "source_id": "source-a",
        "source_title": "Example",
        "source_url": "https://example.org/source.pdf",
        "pdf_page": page,
        "printed_page": page,
    }


class RetrievalTests(unittest.TestCase):
    def test_lexical_search_returns_relevant_chunk_and_no_zero_match(self):
        chunks = [chunk("a", "morador do domicílio na data de referência", 1),
                  chunk("b", "revisão dos setores censitários", 2)]
        search = LexicalRetriever(chunks)
        self.assertEqual(search.search("morador domicílio")[0].chunk["id"], "a")
        self.assertEqual(search.search("zebra"), [])

    def test_page_scoring_deduplicates_chunks_and_checks_all_required_pages(self):
        hits = [SearchResult(chunk("a", "x", 1), 0.9),
                SearchResult(chunk("b", "y", 1), 0.8),
                SearchResult(chunk("c", "z", 2), 0.7)]
        expected = {("source-a", 1), ("source-a", 2)}
        self.assertEqual(score_pages(expected, hits, 2),
                         {"any_page_hit": True, "all_pages_hit": False, "page_recall": 0.5})
        self.assertTrue(score_pages(expected, hits, 3)["all_pages_hit"])

    def test_evaluation_only_scores_answer_questions(self):
        search = LexicalRetriever([chunk("a", "taxa de crescimento anual", 1),
                                   chunk("b", "domicílio particular", 2)])
        questions = [
            {"id": "Q1", "split": "dev", "category": "conceitos", "question": "domicílio particular",
             "expected_behavior": "answer", "evidence": [{"source_id": "source-a", "pdf_page": 2}]},
            {"id": "Q2", "split": "dev", "category": "fora_do_escopo", "question": "população municipal",
             "expected_behavior": "abstain", "evidence": []},
        ]
        report = evaluate(search, questions)
        self.assertEqual(report["splits"]["dev"]["answer_questions"], 1)
        self.assertEqual(report["splits"]["dev"]["unscored_non_answer_questions"], 1)
        self.assertEqual(report["splits"]["dev"]["any_page_hit_at_k"]["1"], 1.0)
        self.assertNotIn("evidence_metrics", report["questions"][1])

    def test_corpus_fingerprint_changes_when_text_changes(self):
        before = [chunk("a", "texto original", 1)]
        after = [chunk("a", "texto alterado", 1)]
        self.assertNotEqual(chunks_sha256(before), chunks_sha256(after))


if __name__ == "__main__":
    unittest.main()
