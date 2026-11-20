"""The project's domain types. Names here must match CONTEXT.md exactly —
if you need a new concept, add it to the glossary first, then here.
"""

from __future__ import annotations

from datetime import date
from enum import StrEnum

from pydantic import BaseModel, Field


class Note(BaseModel):
    """A single Markdown file in a Vault. See CONTEXT.md "Nota"."""

    id: int | None = None
    vault: str
    path: str  # relative to the vault root
    title: str
    folder: str
    area: str | None = None
    note_date: date | None = None
    tags: list[str] = Field(default_factory=list)
    frontmatter: dict = Field(default_factory=dict)
    links: list[str] = Field(default_factory=list)  # outgoing [[wikilink]] titles
    content_hash: str = ""


class Chunk(BaseModel):
    """A piece of a Note that gets indexed and retrieved. See CONTEXT.md
    "Chunk" — always belongs to exactly one Note.
    """

    id: int | None = None
    note_id: int
    ordinal: int
    heading_path: str
    text: str  # what gets shown
    indexed_text: str  # context header + text; what gets embedded/searched
    token_count: int


class Strategy(StrEnum):
    """See CONTEXT.md "Estrategia de recuperación"."""

    FULL_CONTEXT = "full_context"
    LEXICAL = "lexical"
    SEMANTIC = "semantic"
    HYBRID = "hybrid"
    HYBRID_RERANK = "hybrid_rerank"
    AGENTIC = "agentic"


class Filters(BaseModel):
    """See CONTEXT.md "Filtro"."""

    area: str | None = None
    folder: str | None = None
    date_from: date | None = None
    date_to: date | None = None


class Signals(BaseModel):
    """Per-signal breakdown behind a Result's final score. Drives the
    explainable-search web UI (docs/SPEC.md §13).
    """

    lexical_rank: int | None = None
    semantic_rank: int | None = None
    rrf_score: float | None = None
    rerank_score: float | None = None


class SearchResult(BaseModel):
    """A single retrieved Chunk with its score. See CONTEXT.md "Resultado"."""

    chunk_id: int
    note_path: str
    note_title: str
    heading_path: str
    text: str
    score: float
    signals: Signals = Field(default_factory=Signals)


class SearchResponse(BaseModel):
    query: str
    strategy: Strategy
    filters: Filters
    results: list[SearchResult]
    latency_ms: dict[str, float] = Field(default_factory=dict)
