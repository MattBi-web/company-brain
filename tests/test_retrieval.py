"""Retrieval sanity test — requires `company-brain ingest` to have been run
(or runs it itself via the fixture below) so it also doubles as an
end-to-end smoke test for the ingestion pipeline."""
import pytest

from company_brain import config, dense, store
from company_brain.eval_data import EVAL_SET
from company_brain.graph import build_graph
from company_brain.ingest import build_chunks, load_documents
from company_brain.retrieval import retrieve
from company_brain.sparse import build_index


@pytest.fixture(scope="module")
def built_index():
    docs = load_documents()
    chunks = build_chunks(docs)
    embeddings = dense.embed_texts([c.text for c in chunks])
    bm25_retriever = build_index([c.text for c in chunks])
    graph = build_graph(docs)
    return chunks, embeddings, bm25_retriever, graph


def test_corpus_loads():
    docs = load_documents()
    assert len(docs) >= 8, "expected the full sample logistics corpus to be present"


@pytest.mark.parametrize("question,expected_doc", EVAL_SET)
def test_retrieval_hits_expected_source(built_index, question, expected_doc):
    chunks, embeddings, bm25_retriever, graph = built_index
    results = retrieve(question, chunks, embeddings, bm25_retriever, graph, final_k=1)
    assert results, f"no results for: {question}"
    assert results[0].chunk.doc_id == expected_doc, (
        f"question={question!r} expected={expected_doc!r} got={results[0].chunk.doc_id!r}"
    )


def test_hit_rate_is_reasonably_high(built_index):
    chunks, embeddings, bm25_retriever, graph = built_index
    hits = 0
    for question, expected_doc in EVAL_SET:
        results = retrieve(question, chunks, embeddings, bm25_retriever, graph, final_k=1)
        if results and results[0].chunk.doc_id == expected_doc:
            hits += 1
    hit_rate = hits / len(EVAL_SET)
    assert hit_rate >= 0.75, f"hit-rate dropped to {hit_rate:.0%} — check chunking/fusion/graph boost"
