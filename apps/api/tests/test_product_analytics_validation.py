import pytest

from apps.api.app.pilot_product_analytics import (
    PilotProductAnalyticsService,
    ProductAnalyticsValidationError,
    RedisPilotProductAnalyticsRepository,
)


class Redis:
    def __init__(self):
        self.values = {}
        self.sets = {}

    def setex(self, key, ttl, value):
        self.values[key] = value

    def get(self, key):
        return self.values.get(key)

    def sadd(self, key, value):
        self.sets.setdefault(key, set()).add(value)

    def smembers(self, key):
        return self.sets.get(key, set())


def test_invalid_rating_rejected():
    service = PilotProductAnalyticsService(
        repository=RedisPilotProductAnalyticsRepository(
            Redis(),
            prefix="analytics",
        )
    )

    with pytest.raises(ProductAnalyticsValidationError):
        service.submit_feedback(
            feedback_id="f1",
            club_id="c1",
            user_id="u1",
            feature="DASHBOARD",
            rating=6,
            category="USABILITY",
            message="x",
            now=100,
        )
