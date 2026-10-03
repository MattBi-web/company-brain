"""Hybrid retrieval: dense (semantic) + sparse (BM25) fused with Reciprocal
Rank Fusion, nudged by the entity graph, then re-ordered by a cross-encoder
reranker on the short-list before anything reaches the answer composer.

Why RRF rather than a weighted score blend: dense cosine similarity and
BM25 scores live on different, corpus-dependent scales, so averaging them
directly either needs per-query normalization tricks or quietly lets
whichever score happens to be larger dominate. RRF only uses each method's
*rank order*, which is scale-free and a well-established default for
hybrid search.
"""
from dataclasses import dataclass

import numpy as np

from . import config, dense, sparse
from .graph import related_docs_for_query
from .ingest import Chunk


@dataclass
class RetrievedChunk:
    chunk: Chunk
    fused_score: float
    rerank_score: float | None = None


def _rrf_scores(rank_lists: list[list[int]], k: int = config.RRF_K) -> dict[int, float]:
    scores: dict[int, float] = {}
    for ranks in rank_lists:
        for position, idx in enumerate(ranks):
            scores[idx] = scores.get(idx, 0.0) + 1.0 / (k + position + 1)
    return scores


def retrieve(
    query: str,
    chunks: list[Chunk],
    embeddings: np.ndarray,
    bm25_retriever,
    graph,
    top_n: int = config.RERANK_TOP_N,
    final_k: int = config.FINAL_TOP_K,
    use_reranker: bool = True,
) -> list[RetrievedChunk]:
    n = len(chunks)

    # Dense ranking
    query_vec = dense.embed_query(query)
    dense_scores = dense.cosine_scores(query_vec, embeddings)
    dense_rank = list(np.argsort(-dense_scores))

    # Sparse ranking
    sparse_hits = sparse.search(bm25_retriever, query, k=min(n, max(top_n * 3, 20)))
    sparse_rank = [idx for idx, _ in sparse_hits]

    fused = _rrf_scores([dense_rank, sparse_rank])

    # Graph boost: chunks whose document shares entities with the query get nudged up.
    # hops=0 (exact entity match only) is deliberate — 1-hop neighbor expansion sounds
    # like it should help recall, but in practice it rewards entity-*dense* documents
    # (e.g. a rate card mentioning a dozen ports/carriers) regardless of whether they're
    # actually relevant, since expansion pulls in whatever else those entities
    # co-occurred with anywhere in the corpus. Exact match is noisier on recall but
    # doesn't have that systematic bias.
    doc_overlap = related_docs_for_query(graph, query, hops=0)
    if doc_overlap:
        for idx, chunk in enumerate(chunks):
            shared = doc_overlap.get(chunk.doc_id, 0)
            if shared and idx in fused:
                fused[idx] += shared * config.GRAPH_BOOST_PER_SHARED_ENTITY

    ranked_idx = sorted(fused, key=lambda i: -fused[i])[:top_n]
    candidates = [RetrievedChunk(chunk=chunks[i], fused_score=fused[i]) for i in ranked_idx]

    if use_reranker and candidates:
        rerank_scores = dense.rerank(query, [c.chunk.text for c in candidates])
        for c, score in zip(candidates, rerank_scores):
            c.rerank_score = score
        candidates.sort(key=lambda c: -c.rerank_score)

    return candidates[:final_k]
