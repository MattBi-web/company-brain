"""A small, deterministic knowledge graph over the domain's entities.

Rather than pulling in a full NER model for a demo corpus this size, entities
are matched against a curated domain vocabulary (carriers, ports, container
types, Incoterms, lane groups, core concepts). That's a reasonable trade-off
here: the vocabulary is small, closed, and known in advance — exactly the
case where a deterministic matcher beats a statistical one on both
precision and latency. Swapping in a real NER/LLM extractor later is a
drop-in replacement for `extract_entities`.
"""
import re
from collections import defaultdict

import networkx as nx

VOCAB: dict[str, list[str]] = {
    "carrier": ["Maersk", "MSC", "CMA CGM", "Hapag-Lloyd"],
    "port": [
        "Shanghai", "Ningbo", "Shenzhen", "Long Beach", "Oakland",
        "New York/New Jersey", "Savannah", "Rotterdam", "Hamburg",
    ],
    "container_type": [
        "20GP", "40GP", "40HC", "20 Reefer", "40 Reefer", "Reefer",
        "Open Top", "Flat Rack", "Tank Container",
    ],
    "incoterm": ["EXW", "FOB", "CIF", "CPT", "DAP", "DDP"],
    "lane_group": [
        "Transpacific", "Asia", "North Europe", "Intra-Mediterranean",
        "South America", "US West Coast", "US East Coast",
    ],
    "concept": [
        "demurrage", "detention", "free time", "SLA", "congestion advisory",
        "combined free time", "BAF", "PSS", "rail dray", "intermodal",
    ],
}

# Longest-match-first avoids e.g. "Reefer" shadowing "40 Reefer".
_ALL_TERMS = sorted(
    ((term, etype) for etype, terms in VOCAB.items() for term in terms),
    key=lambda pair: -len(pair[0]),
)
_PATTERN = re.compile(
    r"(?<![\w-])(" + "|".join(re.escape(t) for t, _ in _ALL_TERMS) + r")(?![\w-])",
    re.IGNORECASE,
)
_TERM_TO_TYPE = {t.lower(): (t, etype) for t, etype in _ALL_TERMS}


def extract_entities(text: str) -> list[tuple[str, str]]:
    """Returns deduplicated (canonical_term, entity_type) pairs found in text."""
    found: dict[str, str] = {}
    for match in _PATTERN.finditer(text):
        canonical, etype = _TERM_TO_TYPE[match.group(1).lower()]
        found[canonical] = etype
    return sorted(found.items())


def build_graph(docs: dict[str, dict]) -> nx.Graph:
    """Builds a bipartite-ish graph: document nodes + entity nodes, with
    doc→entity edges and entity↔entity co-occurrence edges (weighted by how
    often two entities appear together in the same document)."""
    g = nx.Graph()
    doc_entities: dict[str, list[tuple[str, str]]] = {}

    for doc_id, doc in docs.items():
        g.add_node(doc_id, kind="document", title=doc["title"])
        entities = extract_entities(doc["text"])
        doc_entities[doc_id] = entities
        for term, etype in entities:
            if not g.has_node(term):
                g.add_node(term, kind="entity", entity_type=etype)
            g.add_edge(doc_id, term, kind="mentions")

    cooc_counts: dict[tuple[str, str], int] = defaultdict(int)
    for entities in doc_entities.values():
        terms = sorted({term for term, _ in entities})
        for i, a in enumerate(terms):
            for b in terms[i + 1 :]:
                cooc_counts[(a, b)] += 1

    for (a, b), count in cooc_counts.items():
        g.add_edge(a, b, kind="co-occurs", weight=count)

    return g


def related_docs_for_query(g: nx.Graph, query_text: str, hops: int = 1) -> dict[str, int]:
    """Given a query, extracts its entities and returns {doc_id: shared_entity_count}
    for every document connected to those entities (or their 1-hop neighbors)."""
    query_entities = {term for term, _ in extract_entities(query_text)}
    if not query_entities:
        return {}

    expanded = set(query_entities)
    if hops >= 1:
        for term in list(query_entities):
            if g.has_node(term):
                expanded |= {n for n in g.neighbors(term) if g.nodes[n].get("kind") == "entity"}

    scores: dict[str, int] = defaultdict(int)
    for term in expanded:
        if not g.has_node(term):
            continue
        for neighbor in g.neighbors(term):
            if g.nodes[neighbor].get("kind") == "document":
                scores[neighbor] += 1
    return dict(scores)


def top_entities(g: nx.Graph, n: int = 15) -> list[tuple[str, str, int]]:
    """Returns the n entities mentioned in the most documents, as (term, type, doc_count)."""
    rows = []
    for node, data in g.nodes(data=True):
        if data.get("kind") != "entity":
            continue
        doc_count = sum(1 for nb in g.neighbors(node) if g.nodes[nb].get("kind") == "document")
        rows.append((node, data.get("entity_type", "?"), doc_count))
    return sorted(rows, key=lambda r: -r[2])[:n]
