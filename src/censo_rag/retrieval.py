"""Page-cited lexical and semantic retrieval over the ingested IBGE chunks."""

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer


SEMANTIC_MODEL = "intfloat/multilingual-e5-small"
SEMANTIC_MODEL_REVISION = "614241f622f53c4eeff9890bdc4f31cfecc418b3"
SEMANTIC_VECTOR_FORMAT = "e5-query-passage-o4-mean-l2-v1"
SEMANTIC_MODEL_FILES = (
    "config.json", "special_tokens_map.json", "tokenizer_config.json", "tokenizer.json", "onnx/model_O4.onnx"
)


@dataclass(frozen=True)
class SearchResult:
    chunk: dict
    score: float


def load_chunks(path: Path) -> list[dict]:
    if not path.exists():
        raise FileNotFoundError(f"Missing {path}; run scripts/ingest.py first")
    chunks = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not chunks:
        raise ValueError(f"No chunks in {path}")
    required = {"id", "text", "source_id", "source_title", "source_url", "pdf_page", "printed_page"}
    if any(not required.issubset(chunk) or not chunk["text"].strip() for chunk in chunks):
        raise ValueError(f"Invalid chunk in {path}")
    if len({chunk["id"] for chunk in chunks}) != len(chunks):
        raise ValueError(f"Duplicate chunk ID in {path}")
    return chunks


def chunks_sha256(chunks: list[dict]) -> str:
    """Fingerprint the content and ordering used by a search index."""
    content = "".join(json.dumps(chunk, ensure_ascii=False, sort_keys=True) + "\n" for chunk in chunks)
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _rank(chunks: list[dict], scores: np.ndarray, k: int) -> list[SearchResult]:
    if k < 1:
        raise ValueError("k must be positive")
    # Keep the ingestion order as the deterministic tie breaker.
    order = np.argsort(-scores, kind="stable")[:k]
    return [SearchResult(chunks[int(i)], float(scores[i])) for i in order if scores[i] > 0]


class LexicalRetriever:
    """TF-IDF word and word-pair baseline; no model download or API key."""

    def __init__(self, chunks: list[dict]):
        self.chunks = chunks
        self.vectorizer = TfidfVectorizer(strip_accents="unicode", ngram_range=(1, 2), sublinear_tf=True)
        self.matrix = self.vectorizer.fit_transform(chunk["text"] for chunk in chunks)

    def search(self, question: str, k: int = 5) -> list[SearchResult]:
        if not question.strip():
            raise ValueError("Question must not be empty")
        query = self.vectorizer.transform([question])
        scores = (self.matrix @ query.T).toarray().ravel()
        return _rank(self.chunks, scores, k)


class SemanticRetriever:
    """Local multilingual embeddings with a corpus- and model-aware vector cache."""

    def __init__(self, chunks: list[dict], cache_dir: Path):
        try:
            from fastembed import TextEmbedding
            from fastembed.common.model_description import ModelSource, PoolingType
            from huggingface_hub import snapshot_download
        except ImportError as exc:
            raise RuntimeError('Install semantic search with pip install -e ".[semantic]"') from exc

        self.chunks = chunks
        self.model_name = SEMANTIC_MODEL
        cache_dir.mkdir(parents=True, exist_ok=True)
        if SEMANTIC_MODEL not in {m["model"] for m in TextEmbedding.list_supported_models()}:
            TextEmbedding.add_custom_model(
                model=SEMANTIC_MODEL,
                pooling=PoolingType.MEAN,
                normalization=True,
                sources=ModelSource(hf=SEMANTIC_MODEL),
                dim=384,
                model_file="onnx/model_O4.onnx",
            )
        model_cache = cache_dir / "models"
        options = dict(repo_id=SEMANTIC_MODEL, revision=SEMANTIC_MODEL_REVISION,
                       cache_dir=str(model_cache), allow_patterns=SEMANTIC_MODEL_FILES)
        try:
            model_dir = Path(snapshot_download(**options, local_files_only=True))
            if not all((model_dir / name).is_file() for name in SEMANTIC_MODEL_FILES):
                raise FileNotFoundError("Incomplete local embedding model")
        except OSError:
            model_dir = Path(snapshot_download(**options))
        self.model = TextEmbedding(model_name=SEMANTIC_MODEL, specific_model_path=str(model_dir))
        model_key = hashlib.sha256(
            f"{SEMANTIC_MODEL}:{SEMANTIC_MODEL_REVISION}:{SEMANTIC_VECTOR_FORMAT}".encode("utf-8")
        ).hexdigest()[:12]
        self.index_path = cache_dir / f"vectors-{model_key}.npz"
        self.corpus_hash = chunks_sha256(chunks)
        self.cache_hit = False
        self.vectors = self._load_or_build()

    def _load_or_build(self) -> np.ndarray:
        if self.index_path.exists():
            with np.load(self.index_path, allow_pickle=False) as saved:
                if (str(saved["corpus_hash"]) == self.corpus_hash
                        and str(saved["model_name"]) == self.model_name
                        and str(saved["model_revision"]) == SEMANTIC_MODEL_REVISION
                        and str(saved["vector_format"]) == SEMANTIC_VECTOR_FORMAT
                        and len(saved["vectors"]) == len(self.chunks)):
                    self.cache_hit = True
                    return saved["vectors"]
        passages = [f"passage: {chunk['text']}" for chunk in self.chunks]
        vectors = np.asarray(list(self.model.embed(passages)), dtype=np.float32)
        if vectors.ndim != 2 or len(vectors) != len(self.chunks):
            raise ValueError("Embedding model returned the wrong number of vectors")
        vectors /= np.maximum(np.linalg.norm(vectors, axis=1, keepdims=True), 1e-12)
        np.savez_compressed(self.index_path, vectors=vectors, corpus_hash=self.corpus_hash,
                            model_name=self.model_name, model_revision=SEMANTIC_MODEL_REVISION,
                            vector_format=SEMANTIC_VECTOR_FORMAT)
        return vectors

    def search(self, question: str, k: int = 5) -> list[SearchResult]:
        if not question.strip():
            raise ValueError("Question must not be empty")
        query = np.asarray(next(self.model.embed([f"query: {question}"])), dtype=np.float32)
        query /= max(float(np.linalg.norm(query)), 1e-12)
        scores = self.vectors @ query
        return _rank(self.chunks, scores, k)
