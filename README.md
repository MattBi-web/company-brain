# Company Brain

A small "company brain" over internal documents: hybrid retrieval (dense embeddings + BM25, fused with
Reciprocal Rank Fusion), a lightweight entity knowledge graph that nudges retrieval toward documents
sharing the query's entities, a cross-encoder reranker on the shortlist, and a grounded answer composer
with a local/cloud provider split (Anthropic if a key is set, an honest extractive fallback otherwise).

Demonstrated on a logistics/freight knowledge base — SLAs, demurrage/detention policy, Incoterms,
carrier contract terms, a rate card, an escalation playbook — because that's the domain I know from
building intermodal sea-rail product at Amazon. The documents are synthetic (see note below); the
retrieval/graph/rerank pipeline is the real thing.

## Pipeline

```
data/*.md
  │
  ├─ ingest.py        chunk documents along ## section boundaries (keeps tables intact)
  │
  ├─ dense.py          embed chunks (sentence-transformers, CPU)
  ├─ sparse.py          BM25 index (bm25s)
  └─ graph.py           entity extraction (domain vocabulary) → networkx graph
  │
  ▼
retrieval.py   dense rank ⊕ BM25 rank  →  Reciprocal Rank Fusion
                        + graph boost (exact entity overlap between query & doc)
                        → cross-encoder rerank on the shortlist (dense.py)
  │
  ▼
llm.py          grounded answer, cited by source document
                (AnthropicComposer if ANTHROPIC_API_KEY is set, else ExtractiveComposer)
```

## Why RRF, not a weighted score blend

Dense cosine similarity and BM25 scores live on different, corpus-dependent scales. Averaging them
directly either needs per-query score normalization or lets whichever one happens to be larger dominate.
Reciprocal Rank Fusion only uses each method's *rank order*, which is scale-free — a standard, defensible
default for hybrid search without extra tuning.

## Why a vocabulary-matched graph, not a general NER model

The entity set here (carriers, ports, container types, Incoterms, lane groups, core concepts) is small
and known in advance — exactly the case where a deterministic matcher (`graph.py`) beats a statistical
NER model on both precision and latency, with zero extra model weights to load. `extract_entities()` is
a drop-in seam for a real NER/LLM extractor if the entity set ever needs to be open-ended.

The graph boost only counts a chunk's document as related when it shares an entity the query mentioned
*exactly* — not a 1-hop neighbor. A neighbor-expanded version seems like free recall, but it rewards
entity-*dense* documents (a rate card touching a dozen ports and carriers) regardless of whether they're
actually relevant, since expansion pulls in whatever else those entities co-occurred with anywhere in
the corpus. `company-brain eval` is what caught this — it dropped the hit-rate from 9/9 to 5/9 — which is
the reason the eval set exists at all: a retrieval change that "sounds like it should help" needs a
number attached to it, not just a plausible mechanism.

## Why section-aware chunking, not a fixed word-window

These documents lean on markdown tables (rate cards, free-time schedules, SLA thresholds). A fixed
word-count window cuts a table row away from its header mid-sentence, which breaks both BM25 term
proximity and the cross-encoder reranker — "Transpacific (Asia → US West Coast)" and "4 days | 5 days"
can land in different chunks. Splitting on `##` headers keeps each table or policy clause intact as one
retrievable unit (chunks end up uneven in length, which is fine — a policy clause is a more meaningful
unit than 180 words).

## Setup

```bash
pip install -e .
cp .env.example .env   # optional: add ANTHROPIC_API_KEY for composed (not just extractive) answers

company-brain ingest                 # builds the dense index, BM25 index, and entity graph
company-brain ask "How many free demurrage days do we get on Transpacific imports to the US West Coast?"
company-brain ask "What's the SLA transit time from a US West Coast port to the Chicago rail ramp?" --show-passages
company-brain graph                  # inspect the extracted entity graph
company-brain eval                   # retrieval hit-rate against a small hand-labeled question set
```

Without an `ANTHROPIC_API_KEY`, `ask` still runs end to end — it returns the top grounded passages
verbatim (`ExtractiveComposer`) instead of a composed answer, so the retrieval pipeline is fully
demonstrable with zero external dependencies.

## A sample run

Without an API key (extractive mode — the top grounded passages, verbatim, with sources):

```
$ company-brain ask "What combined free-time pool does our Maersk contract give on Transpacific reefer?"

Q: What combined free-time pool does our Maersk contract give on Transpacific reefer?

(source: carrier_contract_summary_maersk)
## Combined free time
This contract uses a combined free-time pool on Transpacific lanes only: 11 days combined (dry),
7 days combined (reefer) — not split demurrage+detention. North Europe lanes remain split (standard
policy).

(source: carrier_contract_summary_maersk)
## Free time terms (overrides the general policy where more favorable)
- Transpacific dry: 5 days demurrage / 6 days detention (one day better than Meridian's general
  policy — negotiated volume tier).
- Transpacific reefer: 3 days demurrage / 4 days detention.
```

With `ANTHROPIC_API_KEY` set, the same query goes through `AnthropicComposer` instead and comes back as
a short, cited paragraph rather than raw passages.

`company-brain eval` reports retrieval hit-rate against the 9-question hand-labeled set in
`eval_data.py` — currently 9/9 after the two fixes above (graph boost scope, section-aware chunking).

## Project layout

```
src/company_brain/
  ingest.py       document loading + chunking
  dense.py        embeddings + cross-encoder reranker (sentence-transformers)
  sparse.py       BM25 index (bm25s)
  graph.py        entity vocabulary, extraction, co-occurrence graph (networkx)
  retrieval.py    RRF fusion + graph boost + rerank
  llm.py          AnthropicComposer / ExtractiveComposer
  store.py        index persistence (chunks.json, dense.npy, bm25/, graph.pkl)
  eval_data.py    hand-labeled (question → expected source) pairs
  cli.py          `company-brain ingest|ask|graph|eval`
tests/
  test_retrieval.py   pytest version of the same eval set, as a CI-style regression check
data/
  *.md            the sample logistics/freight corpus (synthetic, see below)
```

## A note on the sample data

Every document in `data/` is synthetic — invented for this demo, not drawn from any employer's real
policies, contracts, or rates. Carrier and port names are real (public industry facts); every number,
SLA threshold, and contract term is made up for the sake of having something concrete to retrieve and
reason over. The domain knowledge behind *why* these documents look the way they do (what demurrage vs.
detention actually means operationally, how SLA exclusions get negotiated, how an escalation should be
handled) comes from my own experience; none of the content is a real company's data.

## License

MIT — see [LICENSE](LICENSE).
