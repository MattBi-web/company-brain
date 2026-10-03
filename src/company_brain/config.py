"""Central configuration — paths, model names, and chunking/retrieval knobs."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = Path(os.environ.get("COMPANY_BRAIN_DATA_DIR", ROOT / "data"))
INDEX_DIR = Path(os.environ.get("COMPANY_BRAIN_INDEX_DIR", ROOT / ".index"))
STORE_PATH = INDEX_DIR / "store.pkl"

# Chunking
CHUNK_SIZE_WORDS = 180
CHUNK_OVERLAP_WORDS = 40

# Dense embeddings — small, CPU-friendly model (~80MB), good enough for a demo corpus.
DENSE_MODEL_NAME = os.environ.get("COMPANY_BRAIN_DENSE_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

# Cross-encoder reranker, applied to the top-N fused candidates before composing an answer.
RERANKER_MODEL_NAME = os.environ.get(
    "COMPANY_BRAIN_RERANKER_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2"
)
RERANK_TOP_N = 8  # candidates handed to the cross-encoder
FINAL_TOP_K = 4  # passages handed to the answer composer after reranking

# Hybrid fusion (Reciprocal Rank Fusion constant — standard default)
RRF_K = 60

# Graph-based boost: entities shared between the query and a chunk's document nudge
# that chunk's fused rank; this is deliberately a small, transparent boost, not a
# separate scoring path, so retrieval stays easy to reason about.
GRAPH_BOOST_PER_SHARED_ENTITY = 0.01

# LLM composer — Anthropic if a key is present, otherwise a deterministic
# extractive fallback (same local/cloud-provider pattern used in meeting-copilot).
ANTHROPIC_MODEL = os.environ.get("COMPANY_BRAIN_ANTHROPIC_MODEL", "claude-sonnet-4-5")
FORCE_FAKE_LLM = os.environ.get("COMPANY_BRAIN_LLM_FAKE", "0") == "1"
