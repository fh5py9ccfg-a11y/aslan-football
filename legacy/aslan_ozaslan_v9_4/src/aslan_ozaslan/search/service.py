from __future__ import annotations
from collections import OrderedDict
from hashlib import sha256
import json

from aslan_ozaslan.search.models import SearchDocument, SearchQuery, SearchResult
from aslan_ozaslan.search.ranking import SearchRanker

class SearchService:
    def __init__(self, ranker: SearchRanker | None = None, cache_size: int = 256):
        if cache_size <= 0:
            raise ValueError("cache_size pozitif olmalıdır")
        self.ranker = ranker or SearchRanker()
        self.cache_size = cache_size
        self._documents: dict[str, SearchDocument] = {}
        self._cache: OrderedDict[str, list[SearchResult]] = OrderedDict()

    def index(self, documents: list[SearchDocument]) -> None:
        for document in documents:
            self._documents[document.document_id] = document
        self._cache.clear()

    def search(self, query: SearchQuery) -> list[SearchResult]:
        key = self._cache_key(query)
        if key in self._cache:
            self._cache.move_to_end(key)
            return list(self._cache[key])

        results = self.ranker.rank(query, list(self._documents.values()))
        self._cache[key] = list(results)
        self._cache.move_to_end(key)

        while len(self._cache) > self.cache_size:
            self._cache.popitem(last=False)

        return results

    def _cache_key(self, query: SearchQuery) -> str:
        payload = {
            "text": query.text,
            "competition_id": query.competition_id,
            "team_ids": list(query.team_ids),
            "language": query.language,
            "limit": query.limit,
            "index_version": self._index_version(),
        }
        return sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()

    def _index_version(self) -> str:
        ids = sorted(self._documents.keys())
        return sha256("|".join(ids).encode("utf-8")).hexdigest()
