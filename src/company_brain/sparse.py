"""Sparse (BM25) retrieval over the same chunks, via bm25s."""
import re

import bm25s


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def build_index(texts: list[str]) -> bm25s.BM25:
    corpus_tokens = [_tokenize(t) for t in texts]
    retriever = bm25s.BM25()
    retriever.index(corpus_tokens)
    return retriever


def search(retriever: bm25s.BM25, query: str, k: int) -> list[tuple[int, float]]:
    """Returns [(chunk_index, score), ...] for the top-k chunks, sorted desc."""
    query_tokens = _tokenize(query)
    results, scores = retriever.retrieve([query_tokens], k=k)
    return list(zip(results[0].tolist(), scores[0].tolist()))
