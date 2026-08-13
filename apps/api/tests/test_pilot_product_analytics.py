from apps.api.app.pilot_product_analytics import (
    PilotProductAnalyticsService,
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


def build():
    return PilotProductAnalyticsService(
        repository=RedisPilotProductAnalyticsRepository(
            Redis(),
            prefix="analytics",
        )
    )


def test_adoption_and_priority_reports():
    service = build()
    service.record_usage(
        event_id="e1",
        club_id="c1",
        user_id="u1",
        feature="MATCH_INTELLIGENCE",
        action="RUN",
        session_id="s1",
        duration_ms=200,
        success=True,
        now=100,
    )
    service.record_usage(
        event_id="e2",
        club_id="c1",
        user_id="u1",
        feature="MATCH_INTELLIGENCE",
        action="ERROR",
        session_id="s1",
        duration_ms=400,
        success=False,
        now=101,
    )
    service.submit_feedback(
        feedback_id="f1",
        club_id="c1",
        user_id="u1",
        feature="MATCH_INTELLIGENCE",
        rating=2,
        category="ACCURACY",
        message="Tahmin güveni düşük",
        now=102,
    )

    adoption = service.adoption_report(
        report_id="r1",
        club_id="c1",
        now=103,
    )
    priorities = service.improvement_priorities(
        club_id="c1"
    )

    assert adoption.total_events == 2
    assert adoption.most_used_feature == "MATCH_INTELLIGENCE"
    assert priorities[0].priority in {"P0", "P1", "P2", "P3"}
    assert len(priorities[0].reasons) >= 1


def test_weekly_report():
    service = build()
    service.record_usage(
        event_id="e1",
        club_id="c1",
        user_id="u1",
        feature="DASHBOARD",
        action="VIEW",
        session_id="s1",
        now=100,
    )
    service.submit_feedback(
        feedback_id="f1",
        club_id="c1",
        user_id="u1",
        feature="DASHBOARD",
        rating=5,
        category="USABILITY",
        message="İyi",
        now=101,
    )

    report = service.weekly_report(
        report_id="w1",
        club_id="c1",
        week_key="2026-W32",
        now=102,
    )

    assert report.active_users == 1
    assert report.sessions == 1
    assert report.average_rating == 5.0
    assert len(report.top_priorities) == 5
