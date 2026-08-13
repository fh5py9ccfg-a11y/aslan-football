from __future__ import annotations

from dataclasses import dataclass
import json
import time


@dataclass(frozen=True)
class ProductUsageEvent:
    event_id: str
    club_id: str
    user_id: str
    feature: str
    action: str
    session_id: str
    duration_ms: int
    success: bool
    created_at: int


@dataclass(frozen=True)
class PilotFeedback:
    feedback_id: str
    club_id: str
    user_id: str
    feature: str
    rating: int
    category: str
    message: str
    status: str
    created_at: int


@dataclass(frozen=True)
class FeatureAdoptionReport:
    report_id: str
    club_id: str
    total_users: int
    active_users: int
    total_events: int
    feature_usage: tuple[dict, ...]
    most_used_feature: str
    least_used_feature: str
    adoption_score: float
    generated_at: int


@dataclass(frozen=True)
class ImprovementPriority:
    feature: str
    usage_score: float
    satisfaction_score: float
    failure_rate: float
    feedback_volume: int
    priority_score: float
    priority: str
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class WeeklyPilotReport:
    report_id: str
    club_id: str
    week_key: str
    active_users: int
    sessions: int
    usage_events: int
    feedback_items: int
    average_rating: float
    adoption_score: float
    top_priorities: tuple[dict, ...]
    generated_at: int


class ProductAnalyticsValidationError(ValueError):
    pass


class RedisPilotProductAnalyticsRepository:
    def __init__(
        self,
        client,
        *,
        prefix: str = "aslan:pilot-product-analytics",
        ttl_seconds: int = 31_536_000,
    ):
        self.client = client
        self.prefix = prefix
        self.ttl_seconds = ttl_seconds

    def save_usage(self, item: ProductUsageEvent) -> ProductUsageEvent:
        self.client.setex(
            self._usage_key(item.event_id),
            self.ttl_seconds,
            json.dumps(item.__dict__, ensure_ascii=False),
        )
        self.client.sadd(
            self._club_usage_index(item.club_id),
            item.event_id,
        )
        return item

    def list_usage(
        self,
        club_id: str,
    ) -> tuple[ProductUsageEvent, ...]:
        items = []
        for event_id in self.client.smembers(
            self._club_usage_index(club_id)
        ):
            if isinstance(event_id, bytes):
                event_id = event_id.decode("utf-8")
            payload = self.client.get(
                self._usage_key(str(event_id))
            )
            if payload is None:
                continue
            if isinstance(payload, bytes):
                payload = payload.decode("utf-8")
            items.append(
                ProductUsageEvent(**json.loads(payload))
            )
        items.sort(key=lambda item: item.created_at)
        return tuple(items)

    def save_feedback(self, item: PilotFeedback) -> PilotFeedback:
        self.client.setex(
            self._feedback_key(item.feedback_id),
            self.ttl_seconds,
            json.dumps(item.__dict__, ensure_ascii=False),
        )
        self.client.sadd(
            self._club_feedback_index(item.club_id),
            item.feedback_id,
        )
        return item

    def list_feedback(
        self,
        club_id: str,
    ) -> tuple[PilotFeedback, ...]:
        items = []
        for feedback_id in self.client.smembers(
            self._club_feedback_index(club_id)
        ):
            if isinstance(feedback_id, bytes):
                feedback_id = feedback_id.decode("utf-8")
            payload = self.client.get(
                self._feedback_key(str(feedback_id))
            )
            if payload is None:
                continue
            if isinstance(payload, bytes):
                payload = payload.decode("utf-8")
            items.append(
                PilotFeedback(**json.loads(payload))
            )
        items.sort(key=lambda item: item.created_at, reverse=True)
        return tuple(items)

    def _usage_key(self, event_id: str) -> str:
        return f"{self.prefix}:usage:{event_id}"

    def _club_usage_index(self, club_id: str) -> str:
        return f"{self.prefix}:usage-index:{club_id}"

    def _feedback_key(self, feedback_id: str) -> str:
        return f"{self.prefix}:feedback:{feedback_id}"

    def _club_feedback_index(self, club_id: str) -> str:
        return f"{self.prefix}:feedback-index:{club_id}"


class PilotProductAnalyticsService:
    FEATURES = {
        "DASHBOARD",
        "PLAYERS",
        "MATCHES",
        "INTEGRATIONS",
        "MATCH_INTELLIGENCE",
        "PIPELINE",
        "OBSERVABILITY",
        "BACKUP",
    }
    ACTIONS = {
        "VIEW",
        "CREATE",
        "UPDATE",
        "RUN",
        "APPROVE",
        "EXPORT",
        "ERROR",
    }
    FEEDBACK_CATEGORIES = {
        "USABILITY",
        "ACCURACY",
        "PERFORMANCE",
        "MISSING_FEATURE",
        "BUG",
        "OTHER",
    }

    def __init__(self, *, repository):
        self.repository = repository

    def record_usage(
        self,
        *,
        event_id: str,
        club_id: str,
        user_id: str,
        feature: str,
        action: str,
        session_id: str,
        duration_ms: int = 0,
        success: bool = True,
        now: int | None = None,
    ) -> ProductUsageEvent:
        normalized_feature = feature.upper()
        normalized_action = action.upper()
        if normalized_feature not in self.FEATURES:
            raise ProductAnalyticsValidationError(
                "Geçersiz ürün özelliği"
            )
        if normalized_action not in self.ACTIONS:
            raise ProductAnalyticsValidationError(
                "Geçersiz kullanım aksiyonu"
            )
        if duration_ms < 0:
            raise ProductAnalyticsValidationError(
                "Süre negatif olamaz"
            )
        item = ProductUsageEvent(
            event_id=event_id,
            club_id=club_id,
            user_id=user_id.strip(),
            feature=normalized_feature,
            action=normalized_action,
            session_id=session_id.strip(),
            duration_ms=duration_ms,
            success=success,
            created_at=int(now if now is not None else time.time()),
        )
        return self.repository.save_usage(item)

    def submit_feedback(
        self,
        *,
        feedback_id: str,
        club_id: str,
        user_id: str,
        feature: str,
        rating: int,
        category: str,
        message: str,
        now: int | None = None,
    ) -> PilotFeedback:
        normalized_feature = feature.upper()
        normalized_category = category.upper()
        if normalized_feature not in self.FEATURES:
            raise ProductAnalyticsValidationError(
                "Geçersiz ürün özelliği"
            )
        if normalized_category not in self.FEEDBACK_CATEGORIES:
            raise ProductAnalyticsValidationError(
                "Geçersiz geri bildirim kategorisi"
            )
        if not 1 <= rating <= 5:
            raise ProductAnalyticsValidationError(
                "Puan 1 ile 5 arasında olmalıdır"
            )
        item = PilotFeedback(
            feedback_id=feedback_id,
            club_id=club_id,
            user_id=user_id.strip(),
            feature=normalized_feature,
            rating=rating,
            category=normalized_category,
            message=message.strip(),
            status="OPEN",
            created_at=int(now if now is not None else time.time()),
        )
        return self.repository.save_feedback(item)

    def adoption_report(
        self,
        *,
        report_id: str,
        club_id: str,
        now: int | None = None,
    ) -> FeatureAdoptionReport:
        events = self.repository.list_usage(club_id)
        users = {item.user_id for item in events if item.user_id}
        sessions = {item.session_id for item in events if item.session_id}
        feature_rows = []
        for feature in sorted(self.FEATURES):
            feature_events = [item for item in events if item.feature == feature]
            active_users = {item.user_id for item in feature_events if item.user_id}
            success_rate = (
                sum(1 for item in feature_events if item.success)
                / len(feature_events) * 100
                if feature_events
                else 0.0
            )
            feature_rows.append({
                "feature": feature,
                "events": len(feature_events),
                "active_users": len(active_users),
                "success_rate": round(success_rate, 2),
            })

        most_used = max(
            feature_rows,
            key=lambda item: item["events"],
        )["feature"]
        least_used = min(
            feature_rows,
            key=lambda item: item["events"],
        )["feature"]

        feature_coverage = sum(
            1 for row in feature_rows if row["events"] > 0
        ) / len(feature_rows)
        session_factor = min(1.0, len(sessions) / max(1, len(users) * 2))
        adoption_score = (
            feature_coverage * 0.65
            + session_factor * 0.35
        ) * 100

        return FeatureAdoptionReport(
            report_id=report_id,
            club_id=club_id,
            total_users=len(users),
            active_users=len(users),
            total_events=len(events),
            feature_usage=tuple(feature_rows),
            most_used_feature=most_used,
            least_used_feature=least_used,
            adoption_score=round(adoption_score, 2),
            generated_at=int(now if now is not None else time.time()),
        )

    def improvement_priorities(
        self,
        *,
        club_id: str,
    ) -> tuple[ImprovementPriority, ...]:
        events = self.repository.list_usage(club_id)
        feedback = self.repository.list_feedback(club_id)
        total_events = max(1, len(events))
        rows = []

        for feature in sorted(self.FEATURES):
            feature_events = [item for item in events if item.feature == feature]
            feature_feedback = [item for item in feedback if item.feature == feature]
            usage_score = len(feature_events) / total_events * 100
            satisfaction = (
                sum(item.rating for item in feature_feedback)
                / len(feature_feedback) * 20
                if feature_feedback
                else 60.0
            )
            failure_rate = (
                sum(1 for item in feature_events if not item.success)
                / len(feature_events) * 100
                if feature_events
                else 0.0
            )
            feedback_volume = len(feature_feedback)
            priority_score = (
                (100 - satisfaction) * 0.40
                + failure_rate * 0.35
                + min(100.0, feedback_volume * 15.0) * 0.15
                + (100 - min(100.0, usage_score * 4)) * 0.10
            )
            priority = (
                "P0"
                if priority_score >= 70
                else "P1"
                if priority_score >= 50
                else "P2"
                if priority_score >= 30
                else "P3"
            )
            reasons = []
            if satisfaction < 60:
                reasons.append("Kullanıcı memnuniyeti düşük")
            if failure_rate >= 15:
                reasons.append("Başarısız işlem oranı yüksek")
            if feedback_volume >= 3:
                reasons.append("Geri bildirim yoğunluğu yüksek")
            if usage_score < 5:
                reasons.append("Özellik benimsenme oranı düşük")
            if not reasons:
                reasons.append("Acil iyileştirme sinyali yok")
            rows.append(
                ImprovementPriority(
                    feature=feature,
                    usage_score=round(usage_score, 2),
                    satisfaction_score=round(satisfaction, 2),
                    failure_rate=round(failure_rate, 2),
                    feedback_volume=feedback_volume,
                    priority_score=round(priority_score, 2),
                    priority=priority,
                    reasons=tuple(reasons),
                )
            )

        rows.sort(
            key=lambda item: item.priority_score,
            reverse=True,
        )
        return tuple(rows)

    def weekly_report(
        self,
        *,
        report_id: str,
        club_id: str,
        week_key: str,
        now: int | None = None,
    ) -> WeeklyPilotReport:
        events = self.repository.list_usage(club_id)
        feedback = self.repository.list_feedback(club_id)
        users = {item.user_id for item in events if item.user_id}
        sessions = {item.session_id for item in events if item.session_id}
        average_rating = (
            sum(item.rating for item in feedback) / len(feedback)
            if feedback
            else 0.0
        )
        adoption = self.adoption_report(
            report_id=f"{report_id}:adoption",
            club_id=club_id,
            now=now,
        )
        priorities = self.improvement_priorities(
            club_id=club_id
        )[:5]

        return WeeklyPilotReport(
            report_id=report_id,
            club_id=club_id,
            week_key=week_key,
            active_users=len(users),
            sessions=len(sessions),
            usage_events=len(events),
            feedback_items=len(feedback),
            average_rating=round(average_rating, 2),
            adoption_score=adoption.adoption_score,
            top_priorities=tuple(
                {
                    **item.__dict__,
                    "reasons": list(item.reasons),
                }
                for item in priorities
            ),
            generated_at=int(now if now is not None else time.time()),
        )
