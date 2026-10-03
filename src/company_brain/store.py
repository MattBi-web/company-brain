"""Persists and reloads the built index: chunks, dense embeddings, the BM25
index, and the entity graph. Kept as plain files (no external vector DB)
since the demo corpus is small — the retrieval *logic* is the point, not
the storage engine."""
import json
import pickle
from dataclasses import asdict

import bm25s
import networkx as nx
import numpy as np

from . import config
from .ingest import Chunk


def save_store(chunks: list[Chunk], embeddings: np.ndarray, bm25_retriever: bm25s.BM25, graph: nx.Graph) -> None:
    config.INDEX_DIR.mkdir(parents=True, exist_ok=True)

    with open(config.INDEX_DIR / "chunks.json", "w", encoding="utf-8") as f:
        json.dump([asdict(c) for c in chunks], f, ensure_ascii=False)

    np.save(config.INDEX_DIR / "dense.npy", embeddings)

    bm25_retriever.save(str(config.INDEX_DIR / "bm25"))

    with open(config.INDEX_DIR / "graph.pkl", "wb") as f:
        pickle.dump(graph, f)


def load_store() -> tuple[list[Chunk], np.ndarray, bm25s.BM25, nx.Graph]:
    if not config.INDEX_DIR.exists():
        raise FileNotFoundError(
            f"No index found at {config.INDEX_DIR}. Run `company-brain ingest` first."
        )

    with open(config.INDEX_DIR / "chunks.json", encoding="utf-8") as f:
        chunks = [Chunk(**row) for row in json.load(f)]

    embeddings = np.load(config.INDEX_DIR / "dense.npy")

    bm25_retriever = bm25s.BM25.load(str(config.INDEX_DIR / "bm25"), load_corpus=False)

    with open(config.INDEX_DIR / "graph.pkl", "rb") as f:
        graph = pickle.load(f)

    return chunks, embeddings, bm25_retriever, graph
