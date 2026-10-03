"""Answer composition — same local/cloud provider-abstraction pattern used
in the meeting-copilot project: a common interface, a cloud backend
(Anthropic) when a key is available, and a dependency-free extractive
fallback otherwise, so the demo always runs end to end with zero setup."""
import os
from abc import ABC, abstractmethod

from . import config
from .retrieval import RetrievedChunk

SYSTEM_PROMPT = """You are the Company Brain for Meridian Intermodal Logistics, answering internal \
questions grounded ONLY in the provided document excerpts. Rules:
- Answer only from the excerpts given. If they don't contain the answer, say so plainly.
- Cite the source document for every claim, like this: (source: demurrage_detention_policy).
- Be precise with numbers (free-time days, SLA thresholds, rates) — never round or approximate \
figures that are stated exactly in the excerpts.
- Keep the answer tight: a few sentences, not an essay."""


class AnswerComposer(ABC):
    @abstractmethod
    def compose(self, question: str, passages: list[RetrievedChunk]) -> str: ...


def _format_context(passages: list[RetrievedChunk]) -> str:
    blocks = []
    for p in passages:
        blocks.append(f"[source: {p.chunk.doc_id}]\n{p.chunk.text}")
    return "\n\n---\n\n".join(blocks)


class AnthropicComposer(AnswerComposer):
    def __init__(self, model: str = config.ANTHROPIC_MODEL):
        import anthropic

        self._client = anthropic.Anthropic()
        self._model = model

    def compose(self, question: str, passages: list[RetrievedChunk]) -> str:
        context = _format_context(passages)
        response = self._client.messages.create(
            model=self._model,
            max_tokens=500,
            system=SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": f"Document excerpts:\n\n{context}\n\nQuestion: {question}",
                }
            ],
        )
        return "".join(block.text for block in response.content if block.type == "text")


class ExtractiveComposer(AnswerComposer):
    """No API key / forced-fake path: returns the best-matching passage(s)
    verbatim with their source, instead of synthesizing prose. Honest about
    what it is — a retrieval-only fallback, not a model-written answer."""

    def compose(self, question: str, passages: list[RetrievedChunk]) -> str:
        if not passages:
            return "No relevant internal documents were found for that question."
        lines = [
            "[extractive mode — no LLM configured; showing the top grounded passages verbatim]\n"
        ]
        for p in passages:
            lines.append(f"(source: {p.chunk.doc_id})\n{p.chunk.text.strip()}\n")
        return "\n".join(lines)


def get_composer() -> AnswerComposer:
    if config.FORCE_FAKE_LLM or not os.environ.get("ANTHROPIC_API_KEY"):
        return ExtractiveComposer()
    try:
        return AnthropicComposer()
    except Exception:
        return ExtractiveComposer()
