from __future__ import annotations

from dataclasses import dataclass
import json
import math
import statistics
import time


@dataclass(frozen=True)
class DriftSignal:
    model_id: str
    signal_type: str
    severity: str
    score: float
    threshold: float
    detail: str
    detected_at: int


@dataclass(frozen=True)
class ModelHealthSnapshot:
    model_id: str
    samples: int
    accuracy: float
    brier_score: float
    log_loss: float
    mean_confidence: float
    health_score: int
    status: str
    updated_at: int


@dataclass(frozen=True)
class ReviewItem:
    review_id: str
    model_id: str
    reason: str
    severity: str
    status: str
    created_at: int
    closed_at: int | None


class DriftDetector:
    @staticmethod
    def population_stability_index(
        baseline: tuple[float, ...],
        current: tuple[float, ...],
        *,
        bins: int = 10,
    ) -> float:
        if not baseline or not current:
            raise ValueError(
                "Baseline ve current veri boş olamaz"
            )
        if bins < 2:
            raise ValueError(
                "bins en az 2 olmalıdır"
            )

        minimum = min(min(baseline), min(current))
        maximum = max(max(baseline), max(current))
        if math.isclose(minimum, maximum):
            return 0.0

        width = (maximum - minimum) / bins
        epsilon = 1e-6
        psi = 0.0

        for index in range(bins):
            lower = minimum + index * width
            upper = (
                maximum
                if index == bins - 1
                else lower + width
            )

            if index == bins - 1:
                baseline_count = sum(
                    1
                    for value in baseline
                    if lower <= value <= upper
                )
                current_count = sum(
                    1
                    for value in current
                    if lower <= value <= upper
                )
            else:
                baseline_count = sum(
                    1
                    for value in baseline
                    if lower <= value < upper
                )
                current_count = sum(
                    1
                    for value in current
                    if lower <= value < upper
                )

            baseline_ratio = max(
                epsilon,
                baseline_count / len(baseline),
            )
            current_ratio = max(
                epsilon,
                current_count / len(current),
            )

            psi += (
                current_ratio - baseline_ratio
            ) * math.log(
                current_ratio / baseline_ratio
            )

        return round(psi, 6)

    @staticmethod
    def mean_shift(
        baseline: tuple[float, ...],
        current: tuple[float, ...],
    ) -> float:
        if not baseline or not current:
            raise ValueError(
                "Baseline ve current veri boş olamaz"
            )

        baseline_mean = statistics.fmean(baseline)
        current_mean = statistics.fmean(current)
        baseline_std = statistics.pstdev(baseline)

        if math.isclose(baseline_std, 0.0):
            return round(
                abs(current_mean - baseline_mean),
                6,
            )

        return round(
            abs(current_mean - baseline_mean)
            / baseline_std,
            6,
        )

    @staticmethod
    def severity(
        score: float,
        *,
        medium: float,
        high: float,
        critical: float,
    ) -> str:
        if score >= critical:
            return "CRITICAL"
        if score >= high:
            return "HIGH"
        if score >= medium:
            return "MEDIUM"
        return "LOW"


class RedisModelMonitoringRepository:
    def __init__(
        self,
        client,
        *,
        prefix: str = "aslan:model-monitoring",
        ttl_seconds: int = 7_776_000,
    ):
        self.client = client
        self.prefix = prefix
        self.ttl_seconds = ttl_seconds

    def save_health(
        self,
        snapshot: ModelHealthSnapshot,
    ) -> ModelHealthSnapshot:
        self.client.setex(
            self._health_key(snapshot.model_id),
            self.ttl_seconds,
            json.dumps(
                snapshot.__dict__,
                ensure_ascii=False,
                separators=(",", ":"),
            ),
        )
        return snapshot

    def get_health(
        self,
        model_id: str,
    ) -> ModelHealthSnapshot | None:
        payload = self.client.get(
            self._health_key(model_id)
        )
        if payload is None:
            return None
        if isinstance(payload, bytes):
            payload = payload.decode("utf-8")
        return ModelHealthSnapshot(**json.loads(payload))

    def save_signal(
        self,
        signal: DriftSignal,
    ) -> DriftSignal:
        key = (
            f"{signal.model_id}:"
            f"{signal.signal_type}:"
            f"{signal.detected_at}"
        )
        self.client.setex(
            self._signal_key(key),
            self.ttl_seconds,
            json.dumps(
                signal.__dict__,
                ensure_ascii=False,
                separators=(",", ":"),
            ),
        )
        self.client.sadd(
            self._signal_index(signal.model_id),
            key,
        )
        return signal

    def list_signals(
        self,
        model_id: str,
        *,
        limit: int = 100,
    ) -> tuple[DriftSignal, ...]:
        items = []
        for key in self.client.smembers(
            self._signal_index(model_id)
        ):
            if isinstance(key, bytes):
                key = key.decode("utf-8")
            payload = self.client.get(
                self._signal_key(str(key))
            )
            if payload is None:
                continue
            if isinstance(payload, bytes):
                payload = payload.decode("utf-8")
            items.append(
                DriftSignal(**json.loads(payload))
            )
        items.sort(
            key=lambda item: item.detected_at,
            reverse=True,
        )
        return tuple(items[:limit])

    def save_review(
        self,
        review: ReviewItem,
    ) -> ReviewItem:
        self.client.setex(
            self._review_key(review.review_id),
            self.ttl_seconds,
            json.dumps(
                review.__dict__,
                ensure_ascii=False,
                separators=(",", ":"),
            ),
        )
        self.client.sadd(
            self._review_index(),
            review.review_id,
        )
        return review

    def list_reviews(
        self,
        *,
        status: str | None = None,
        limit: int = 100,
    ) -> tuple[ReviewItem, ...]:
        items = []
        for review_id in self.client.smembers(
            self._review_index()
        ):
            if isinstance(review_id, bytes):
                review_id = review_id.decode("utf-8")
            payload = self.client.get(
                self._review_key(str(review_id))
            )
            if payload is None:
                continue
            if isinstance(payload, bytes):
                payload = payload.decode("utf-8")
            review = ReviewItem(**json.loads(payload))
            if status is None or review.status == status:
                items.append(review)
        items.sort(
            key=lambda item: item.created_at,
            reverse=True,
        )
        return tuple(items[:limit])

    def _health_key(self, model_id: str) -> str:
        return f"{self.prefix}:health:{model_id}"

    def _signal_key(self, key: str) -> str:
        return f"{self.prefix}:signal:{key}"

    def _signal_index(self, model_id: str) -> str:
        return f"{self.prefix}:signals:{model_id}"

    def _review_key(self, review_id: str) -> str:
        return f"{self.prefix}:review:{review_id}"

    def _review_index(self) -> str:
        return f"{self.prefix}:reviews"


class ModelMonitoringService:
    def __init__(
        self,
        *,
        repository,
    ):
        self.repository = repository

    def update_health(
        self,
        *,
        model_id: str,
        probabilities: tuple[float, ...],
        outcomes: tuple[int, ...],
        now: int | None = None,
    ) -> ModelHealthSnapshot:
        if len(probabilities) != len(outcomes):
            raise ValueError(
                "Probability ve outcome uzunlukları eşit olmalıdır"
            )
        if not probabilities:
            raise ValueError(
                "En az bir örnek gereklidir"
            )

        eps = 1e-12
        brier_total = 0.0
        log_loss_total = 0.0
        correct = 0

        for probability, outcome in zip(
            probabilities,
            outcomes,
        ):
            if not 0 <= probability <= 1:
                raise ValueError(
                    "Probability 0 ile 1 arasında olmalıdır"
                )
            if outcome not in {0, 1}:
                raise ValueError(
                    "Outcome 0 veya 1 olmalıdır"
                )

            brier_total += (
                probability - outcome
            ) ** 2
            clipped = min(
                1 - eps,
                max(eps, probability),
            )
            log_loss_total += -(
                outcome * math.log(clipped)
                + (1 - outcome)
                * math.log(1 - clipped)
            )
            correct += int(
                (probability >= 0.5) == bool(outcome)
            )

        count = len(probabilities)
        accuracy = correct / count
        brier = brier_total / count
        log_loss = log_loss_total / count
        mean_confidence = statistics.fmean(
            probabilities
        )

        health_score = round(
            100
            - 45 * brier
            - 20 * min(log_loss, 2.0)
            + 20 * accuracy
        )
        health_score = max(
            0,
            min(100, health_score),
        )

        if health_score >= 80:
            status = "HEALTHY"
        elif health_score >= 60:
            status = "DEGRADED"
        else:
            status = "UNHEALTHY"

        current = int(
            now if now is not None
            else time.time()
        )
        snapshot = ModelHealthSnapshot(
            model_id=model_id,
            samples=count,
            accuracy=round(accuracy, 6),
            brier_score=round(brier, 6),
            log_loss=round(log_loss, 6),
            mean_confidence=round(
                mean_confidence,
                6,
            ),
            health_score=health_score,
            status=status,
            updated_at=current,
        )
        return self.repository.save_health(snapshot)

    def detect_prediction_drift(
        self,
        *,
        model_id: str,
        baseline: tuple[float, ...],
        current: tuple[float, ...],
        threshold: float = 0.2,
        now: int | None = None,
    ) -> DriftSignal:
        score = DriftDetector.population_stability_index(
            baseline,
            current,
        )
        severity = DriftDetector.severity(
            score,
            medium=threshold,
            high=0.5,
            critical=1.0,
        )
        signal = DriftSignal(
            model_id=model_id,
            signal_type="PREDICTION_DRIFT",
            severity=severity,
            score=score,
            threshold=threshold,
            detail=(
                "Prediction dağılımı PSI ile karşılaştırıldı"
            ),
            detected_at=int(
                now if now is not None
                else time.time()
            ),
        )
        self.repository.save_signal(signal)
        self._enqueue_review_if_needed(signal)
        return signal

    def detect_feature_drift(
        self,
        *,
        model_id: str,
        feature_name: str,
        baseline: tuple[float, ...],
        current: tuple[float, ...],
        threshold: float = 1.0,
        now: int | None = None,
    ) -> DriftSignal:
        score = DriftDetector.mean_shift(
            baseline,
            current,
        )
        severity = DriftDetector.severity(
            score,
            medium=threshold,
            high=2.0,
            critical=3.0,
        )
        signal = DriftSignal(
            model_id=model_id,
            signal_type=f"FEATURE_DRIFT:{feature_name}",
            severity=severity,
            score=score,
            threshold=threshold,
            detail=(
                "Feature mean shift standart sapma cinsinden ölçüldü"
            ),
            detected_at=int(
                now if now is not None
                else time.time()
            ),
        )
        self.repository.save_signal(signal)
        self._enqueue_review_if_needed(signal)
        return signal

    def shadow_compare(
        self,
        *,
        champion_probabilities: tuple[float, ...],
        shadow_probabilities: tuple[float, ...],
    ) -> dict:
        if len(champion_probabilities) != len(
            shadow_probabilities
        ):
            raise ValueError(
                "Champion ve shadow örnek sayıları eşit olmalıdır"
            )
        if not champion_probabilities:
            raise ValueError(
                "En az bir örnek gereklidir"
            )

        differences = [
            abs(champion - shadow)
            for champion, shadow in zip(
                champion_probabilities,
                shadow_probabilities,
            )
        ]
        return {
            "samples": len(differences),
            "mean_absolute_difference": round(
                statistics.fmean(differences),
                6,
            ),
            "max_difference": round(
                max(differences),
                6,
            ),
        }

    def _enqueue_review_if_needed(
        self,
        signal: DriftSignal,
    ) -> None:
        if signal.severity not in {
            "HIGH",
            "CRITICAL",
        }:
            return

        review = ReviewItem(
            review_id=(
                f"{signal.model_id}:"
                f"{signal.signal_type}:"
                f"{signal.detected_at}"
            ),
            model_id=signal.model_id,
            reason=signal.detail,
            severity=signal.severity,
            status="OPEN",
            created_at=signal.detected_at,
            closed_at=None,
        )
        self.repository.save_review(review)
