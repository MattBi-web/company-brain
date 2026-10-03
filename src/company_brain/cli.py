"""Command-line interface: `company-brain ingest|ask|graph|eval`."""
import typer
from rich.console import Console
from rich.table import Table

from . import config, dense, store
from .graph import build_graph, top_entities
from .ingest import build_chunks, load_documents
from .retrieval import retrieve

app = typer.Typer(add_completion=False, help="Company Brain — hybrid RAG + knowledge graph over internal docs.")
console = Console()


@app.command()
def ingest():
    """Build the dense index, BM25 index, and entity graph from data/*.md."""
    docs = load_documents()
    if not docs:
        console.print(f"[red]No documents found in {config.DATA_DIR}[/red]")
        raise typer.Exit(1)

    chunks = build_chunks(docs)
    console.print(f"Loaded [bold]{len(docs)}[/bold] documents → [bold]{len(chunks)}[/bold] chunks")

    console.print("Embedding chunks (dense)...")
    embeddings = dense.embed_texts([c.text for c in chunks])

    console.print("Indexing chunks (BM25)...")
    from . import sparse

    bm25_retriever = sparse.build_index([c.text for c in chunks])

    console.print("Building entity graph...")
    graph = build_graph(docs)

    store.save_store(chunks, embeddings, bm25_retriever, graph)
    console.print(f"[green]Index saved to {config.INDEX_DIR}[/green]")

    table = Table(title="Top entities across the corpus")
    table.add_column("Entity")
    table.add_column("Type")
    table.add_column("Mentioned in # docs")
    for term, etype, count in top_entities(graph, n=10):
        table.add_row(term, etype, str(count))
    console.print(table)


@app.command()
def ask(
    question: str,
    show_passages: bool = typer.Option(False, "--show-passages", help="Print the retrieved passages too."),
    no_rerank: bool = typer.Option(False, "--no-rerank", help="Skip the cross-encoder rerank step."),
):
    """Ask the Company Brain a question, grounded in the ingested documents."""
    from . import llm

    chunks, embeddings, bm25_retriever, graph = store.load_store()
    results = retrieve(question, chunks, embeddings, bm25_retriever, graph, use_reranker=not no_rerank)

    if show_passages:
        table = Table(title="Retrieved passages")
        table.add_column("Source")
        table.add_column("Fused")
        table.add_column("Rerank")
        table.add_column("Excerpt")
        for r in results:
            table.add_row(
                r.chunk.doc_id,
                f"{r.fused_score:.3f}",
                f"{r.rerank_score:.3f}" if r.rerank_score is not None else "—",
                r.chunk.text[:90].replace("\n", " ") + "…",
            )
        console.print(table)

    composer = llm.get_composer()
    answer = composer.compose(question, results)
    console.print(f"\n[bold]Q:[/bold] {question}\n")
    console.print(answer)


@app.command()
def graph():
    """Show the top entities in the knowledge graph (sanity-check the extraction)."""
    _, _, _, g = store.load_store()
    table = Table(title="Entity graph — top entities by document coverage")
    table.add_column("Entity")
    table.add_column("Type")
    table.add_column("Docs")
    for term, etype, count in top_entities(g, n=25):
        table.add_row(term, etype, str(count))
    console.print(table)


@app.command(name="eval")
def eval_cmd():
    """Run the built-in retrieval sanity-check and report hit-rate."""
    from .eval_data import EVAL_SET

    chunks, embeddings, bm25_retriever, g = store.load_store()
    hits = 0
    table = Table(title="Retrieval eval")
    table.add_column("Question")
    table.add_column("Expected source")
    table.add_column("Top result")
    table.add_column("Hit?")

    for question, expected_doc in EVAL_SET:
        results = retrieve(question, chunks, embeddings, bm25_retriever, g, final_k=1)
        top_doc = results[0].chunk.doc_id if results else "—"
        hit = top_doc == expected_doc
        hits += hit
        table.add_row(question, expected_doc, top_doc, "✅" if hit else "❌")

    console.print(table)
    console.print(f"\nHit-rate: [bold]{hits}/{len(EVAL_SET)}[/bold]")


if __name__ == "__main__":
    app()
