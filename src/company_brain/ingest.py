"""Load the document set and split it into chunks along markdown section
boundaries (## headers), falling back to a word-window split only for
sections that are themselves too long.

Why section-aware rather than a blind word-window: these documents lean
heavily on markdown tables (rate cards, free-time schedules, SLA
thresholds). A fixed word-count window cuts a table row away from its
header mid-sentence — which breaks both BM25 term proximity and the
cross-encoder reranker, since "Transpacific (Asia → US West Coast)" and
"4 days | 5 days" can end up in different chunks. Splitting on headers
keeps each table or policy clause intact as one retrievable unit, at the
cost of chunks having uneven length — a worthwhile trade for this kind of
structured policy content. Each chunk is prefixed with the document title
so it stays identifiable out of context (a cheap, standard RAG trick).
"""
import re
from dataclasses import dataclass
from pathlib import Path

from . import config


@dataclass
class Chunk:
    chunk_id: str
    doc_id: str
    doc_title: str
    text: str
    position: int  # chunk index within its document


def _doc_title(text: str, fallback: str) -> str:
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("#"):
            return line.lstrip("#").strip()
    return fallback


_SECTION_SPLIT = re.compile(r"\n(?=##\s)")


def _split_sections(text: str) -> list[str]:
    """Splits on second-level (##) headers; the preamble before the first
    one (title + intro) stays attached to the first section."""
    # Drop the top-level "# Title" line — it's carried separately as doc_title.
    body = re.sub(r"^#\s+.*\n", "", text.lstrip(), count=1)
    parts = [p.strip() for p in _SECTION_SPLIT.split(body) if p.strip()]
    return parts or [body.strip()]


def _word_chunks(text: str, size: int, overlap: int) -> list[str]:
    words = text.split()
    if not words:
        return []
    step = max(size - overlap, 1)
    chunks = []
    for start in range(0, len(words), step):
        piece = words[start : start + size]
        if not piece:
            break
        chunks.append(" ".join(piece))
        if start + size >= len(words):
            break
    return chunks


def load_documents(data_dir: Path | None = None) -> dict[str, dict]:
    """Returns {doc_id: {"title": str, "text": str, "path": Path}}."""
    data_dir = data_dir or config.DATA_DIR
    docs: dict[str, dict] = {}
    for path in sorted(Path(data_dir).glob("*.md")):
        text = path.read_text(encoding="utf-8")
        doc_id = path.stem
        docs[doc_id] = {
            "title": _doc_title(text, fallback=doc_id),
            "text": text,
            "path": path,
        }
    return docs


def build_chunks(docs: dict[str, dict]) -> list[Chunk]:
    chunks: list[Chunk] = []
    for doc_id, doc in docs.items():
        sections = _split_sections(doc["text"])
        position = 0
        for section in sections:
            words = section.split()
            # Oversized sections still get word-windowed, so one giant section
            # can't become a single unwieldy chunk — but in this corpus every
            # section is already well under the limit.
            pieces = (
                [section]
                if len(words) <= config.CHUNK_SIZE_WORDS * 1.3
                else _word_chunks(section, config.CHUNK_SIZE_WORDS, config.CHUNK_OVERLAP_WORDS)
            )
            for piece in pieces:
                chunks.append(
                    Chunk(
                        chunk_id=f"{doc_id}::{position}",
                        doc_id=doc_id,
                        doc_title=doc["title"],
                        text=f"{doc['title']}\n{piece}",
                        position=position,
                    )
                )
                position += 1
    return chunks
