from __future__ import annotations
from datetime import datetime, timezone
from math import exp

from aslan_ozaslan.search.models import SearchDocument, SearchQuery, SearchResult
from aslan_ozaslan.search.normalizer import QueryNormalizer

class SearchRanker:
    def __init__(self, normalizer: QueryNormalizer | None = None):
        self.normalizer = normalizer or QueryNormalizer()

    def rank(self, query: SearchQuery, documents: list[SearchDocument]) -> list[SearchResult]:
        terms = set(self.normalizer.tokens(query.text))
        if not terms:
            return []

        now = datetime.now(timezone.utc)
        results: list[SearchResult] = []

        for document in documents:
            title = self.normalizer.normalize(document.title)
            body = self.normalizer.normalize(document.body)
            title_terms = set(title.split())
            body_terms = set(body.split())

            matched = sorted(terms & (title_terms | body_terms))
            if not matched:
                continue

            title_match = len(terms & title_terms) / len(terms)
            body_match = len(terms & body_terms) / len(terms)

            published = document.published_at
            if published.tzinfo is None:
                published = published.replace(tzinfo=timezone.utc)
            age_days = max(0.0, (now - published).total_seconds() / 86400)
            freshness = exp(-age_days / 30.0)

            team_boost = 0.0
            doc_team_ids = set(document.metadata.get("team_ids", []))
            if query.team_ids and set(query.team_ids) & doc_team_ids:
                team_boost = 0.20

            competition_boost = 0.0
            if query.competition_id and document.metadata.get("competition_id") == query.competition_id:
                competition_boost = 0.15

            score = (
                0.35 * title_match
                + 0.25 * body_match
                + 0.20 * max(0.0, min(document.trust_score, 1.0))
                + 0.10 * freshness
                + team_boost
                + competition_boost
            )

            results.append(
                SearchResult(
                    document_id=document.document_id,
                    title=document.title,
                    source=document.source,
                    score=round(score, 4),
                    matched_terms=tuple(matched),
                    metadata=document.metadata,
                )
            )

        results.sort(key=lambda item: (-item.score, item.document_id))
        return results[: max(1, min(query.limit, 100))]
