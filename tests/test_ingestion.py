import unittest

from censo_rag.chunking import chunk_words, normalize_text
from censo_rag.ingestion import selected_text


MAIN = {"id": "ibge-censo2022-primeiros-resultados"}
NOTE = {"id": "ibge-censo2022-nota-revisao-01"}


class IngestionTests(unittest.TestCase):
    def test_main_source_boundaries_exclude_outside_sections(self):
        first = selected_text(MAIN, 11, "6\nNotas técnicas\nData de referência.\n")
        last = selected_text(MAIN, 19, "14\nTaxa média de crescimento anual.\nTratamento dos dados\nNão incluir.")
        self.assertEqual(first, "Notas técnicas Data de referência.")
        self.assertEqual(last, "Taxa média de crescimento anual.")

    def test_missing_boundary_fails_loudly(self):
        with self.assertRaises(ValueError):
            selected_text(MAIN, 19, "14\nSem título de encerramento")

    def test_note_header_is_removed(self):
        result = selected_text(NOTE, 6, "Censo Demográfico 2022\nNota metodológica n. 01\n6\nIntrodução\nTexto.")
        self.assertEqual(result, "Introdução Texto.")

    def test_chunks_overlap_and_do_not_drop_words(self):
        chunks = chunk_words("um dois três quatro cinco seis sete", max_words=4, overlap_words=2)
        self.assertEqual(chunks, ["um dois três quatro", "três quatro cinco seis", "cinco seis sete"])

    def test_line_wrap_cleaning_preserves_numbers(self):
        self.assertEqual(normalize_text("municí-\npios 2022\n  31/07"), "municípios 2022 31/07")


if __name__ == "__main__":
    unittest.main()
