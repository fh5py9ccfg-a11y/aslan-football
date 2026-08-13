import sys, unittest
from datetime import datetime, timezone, timedelta
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aslan_ozaslan.search import (
    QueryNormalizer, SearchDocument, SearchQuery, SearchRanker, SearchService
)

class SearchTests(unittest.TestCase):
    def setUp(self):
        now = datetime.now(timezone.utc)
        self.documents = [
            SearchDocument(
                document_id="1",
                title="Galatasaray sakatlık raporu",
                body="Takımın son kadro durumu ve sakat oyuncular",
                source="official",
                published_at=now - timedelta(hours=2),
                trust_score=1.0,
                metadata={"team_ids": ["gs"], "competition_id": "tr-super-lig"},
            ),
            SearchDocument(
                document_id="2",
                title="Galatasaray maç yorumu",
                body="Genel taraftar değerlendirmesi",
                source="forum",
                published_at=now - timedelta(days=10),
                trust_score=0.3,
                metadata={"team_ids": ["gs"], "competition_id": "tr-super-lig"},
            ),
            SearchDocument(
                document_id="3",
                title="Fenerbahçe antrenman haberi",
                body="Takım çalışmasını tamamladı",
                source="official",
                published_at=now - timedelta(hours=1),
                trust_score=1.0,
                metadata={"team_ids": ["fb"], "competition_id": "tr-super-lig"},
            ),
        ]

    def test_turkish_normalization(self):
        normalizer = QueryNormalizer()
        self.assertEqual(normalizer.normalize("İSTANBUL Şampiyonu"), "istanbul sampiyonu")

    def test_official_recent_document_ranks_higher(self):
        results = SearchRanker().rank(
            SearchQuery("Galatasaray sakatlık", competition_id="tr-super-lig", team_ids=("gs",)),
            self.documents,
        )
        self.assertEqual(results[0].document_id, "1")

    def test_unrelated_documents_are_filtered(self):
        results = SearchRanker().rank(SearchQuery("Galatasaray"), self.documents)
        self.assertNotIn("3", [item.document_id for item in results])

    def test_cache_is_invalidated_after_reindex(self):
        service = SearchService(cache_size=2)
        service.index(self.documents[:1])
        first = service.search(SearchQuery("Galatasaray"))
        self.assertEqual(len(first), 1)
        service.index(self.documents)
        second = service.search(SearchQuery("Fenerbahçe"))
        self.assertEqual(len(second), 1)

    def test_empty_query_returns_no_results(self):
        service = SearchService()
        service.index(self.documents)
        self.assertEqual(service.search(SearchQuery("   ")), [])

if __name__ == "__main__":
    unittest.main()
