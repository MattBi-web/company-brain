"""Dense embeddings via a small sentence-transformers model, plus the
cross-encoder reranker applied to the fused shortlist."""
from functools import lru_cache

import numpy as np

from . import config


@lru_cache(maxsize=1)
def _embedder():
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(config.DENSE_MODEL_NAME)


@lru_cache(maxsize=1)
def _reranker():
    from sentence_transformers import CrossEncoder

    return CrossEncoder(config.RERANKER_MODEL_NAME)


def embed_texts(texts: list[str]) -> np.ndarray:
    model = _embedder()
    vecs = model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
    return np.asarray(vecs, dtype=np.float32)


def embed_query(text: str) -> np.ndarray:
    return embed_texts([text])[0]


def cosine_scores(query_vec: np.ndarray, matrix: np.ndarray) -> np.ndarray:
    # Vectors are already L2-normalized, so dot product == cosine similarity.
    return matrix @ query_vec


def rerank(query: str, candidates: list[str]) -> list[float]:
    """Cross-encoder relevance scores for (query, candidate) pairs — higher is
    more relevant. Only called on a short candidate list (see RERANK_TOP_N)."""
    model = _reranker()
    pairs = [(query, c) for c in candidates]
    scores = model.predict(pairs)
    return [float(s) for s in scores]
