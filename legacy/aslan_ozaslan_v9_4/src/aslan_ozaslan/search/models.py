from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from typing import Any

@dataclass(frozen=True)
class SearchQuery:
    text: str
    competition_id: str | None = None
    team_ids: tuple[str, ...] = ()
    language: str = "tr"
    limit: int = 20

@dataclass(frozen=True)
class SearchDocument:
    document_id: str
    title: str
    body: str
    source: str
    published_at: datetime
    trust_score: float
    metadata: dict[str, Any]

@dataclass(frozen=True)
class SearchResult:
    document_id: str
    title: str
    source: str
    score: float
    matched_terms: tuple[str, ...]
    metadata: dict[str, Any]
