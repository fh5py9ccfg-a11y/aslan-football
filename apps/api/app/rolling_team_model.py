from __future__ import annotations

from dataclasses import dataclass
import json
import math
import statistics
import time

from .real_data_training import (
    HistoricalMatch,
    RealDataTrainingService,
    RealDataValidationError,
)


OUTCOMES = ("HOME", "DRAW", "AWAY")


@dataclass(frozen=True)
class RollingFeatureRow:
    match_id: str
    kickoff_at: int
    competition: str
    home_team: str
    away_team: str
    features: tuple[float, ...]
    label: str


@dataclass(frozen=True)
class RollingModel:
    model_id: str
    competition: str
    feature_names: tuple[str, ...]
    means: tuple[float, ...]
    scales: tuple[float, ...]
    weights: tuple[tuple[float, ...], ...]
    biases: tuple[float, ...]
    temperature: float
    training_rows: int
    validation_rows: int
    validation_accuracy: float
    validation_log_loss: float
    validation_brier_score: float
    generated_at: int


@dataclass(frozen=True)
class ModelComparisonReport:
    report_id: str
    competition: str
    rolling_accuracy: float
    rolling_log_loss: float
    rolling_brier: float
    ensemble_accuracy: float
    ensemble_log_loss: float
    ensemble_brier: float
    winner: str
    generated_at: int


class RollingTeamModelService:
    FEATURE_NAMES = (
        "home_xg",
        "away_xg",
        "elo_difference",
        "home_points_last5",
        "away_points_last5",
        "home_goal_diff_last5",
        "away_goal_diff_last5",
        "home_xg_diff_last5",
        "away_xg_diff_last5",
        "home_matches_seen",
        "away_matches_seen",
    )

    def __init__(self):
        self.base = RealDataTrainingService()

    def build_rows(
        self,
        *,
        csv_text: str,
        competition: str,
        minimum_history: int = 3,
    ) -> tuple[RollingFeatureRow, ...]:
        matches, _ = self.base.parse_historical_csv(csv_text)
        selected = [
            item for item in matches
            if item.competition.lower() == competition.lower()
        ]
        if len(selected) < 20:
            raise RealDataValidationError(
                "Rolling model için en az 20 maç gerekli"
            )

        history: dict[str, list[dict]] = {}
        rows = []
        for item in selected:
            home_history = history.get(item.home_team, [])
            away_history = history.get(item.away_team, [])

            if (
                len(home_history) >= minimum_history
                and len(away_history) >= minimum_history
            ):
                home_stats = self._rolling_stats(home_history[-5:])
                away_stats = self._rolling_stats(away_history[-5:])
                rows.append(
                    RollingFeatureRow(
                        match_id=item.match_id,
                        kickoff_at=item.kickoff_at,
                        competition=item.competition,
                        home_team=item.home_team,
                        away_team=item.away_team,
                        features=(
                            item.home_xg,
                            item.away_xg,
                            (item.home_elo - item.away_elo) / 400.0,
                            home_stats["points"],
                            away_stats["points"],
                            home_stats["goal_diff"],
                            away_stats["goal_diff"],
                            home_stats["xg_diff"],
                            away_stats["xg_diff"],
                            float(len(home_history)),
                            float(len(away_history)),
                        ),
                        label=self.base._result(
                            item.home_goals,
                            item.away_goals,
                        ),
                    )
                )

            self._append_history(
                history,
                team=item.home_team,
                goals_for=item.home_goals,
                goals_against=item.away_goals,
                xg_for=item.home_xg,
                xg_against=item.away_xg,
            )
            self._append_history(
                history,
                team=item.away_team,
                goals_for=item.away_goals,
                goals_against=item.home_goals,
                xg_for=item.away_xg,
                xg_against=item.home_xg,
            )

        if len(rows) < 12:
            raise RealDataValidationError(
                "Yeterli takım geçmişi oluşmadı"
            )
        return tuple(rows)

    def train(
        self,
        *,
        model_id: str,
        csv_text: str,
        competition: str,
        validation_fraction: float = 0.25,
        epochs: int = 500,
        learning_rate: float = 0.05,
        l2: float = 0.002,
        now: int | None = None,
    ) -> RollingModel:
        rows = list(
            self.build_rows(
                csv_text=csv_text,
                competition=competition,
            )
        )
        split = max(
            9,
            int(len(rows) * (1.0 - validation_fraction)),
        )
        split = min(split, len(rows) - 3)
        train_rows = rows[:split]
        validation_rows = rows[split:]

        means, scales = self._fit_scaler(
            [row.features for row in train_rows]
        )
        x_train = [
            self._scale(row.features, means, scales)
            for row in train_rows
        ]
        y_train = [OUTCOMES.index(row.label) for row in train_rows]

        weights = [
            [0.0 for _ in self.FEATURE_NAMES]
            for _ in OUTCOMES
        ]
        biases = [0.0, 0.0, 0.0]

        for _ in range(epochs):
            grad_w = [
                [0.0 for _ in self.FEATURE_NAMES]
                for _ in OUTCOMES
            ]
            grad_b = [0.0, 0.0, 0.0]

            for features, target in zip(x_train, y_train):
                probs = self._softmax(
                    [
                        biases[class_index]
                        + sum(
                            weight * value
                            for weight, value in zip(
                                weights[class_index],
                                features,
                            )
                        )
                        for class_index in range(3)
                    ]
                )
                for class_index in range(3):
                    error = probs[class_index] - (
                        1.0 if class_index == target else 0.0
                    )
                    grad_b[class_index] += error
                    for feature_index, value in enumerate(features):
                        grad_w[class_index][feature_index] += (
                            error * value
                            + l2 * weights[class_index][feature_index]
                        )

            count = len(x_train)
            for class_index in range(3):
                biases[class_index] -= (
                    learning_rate * grad_b[class_index] / count
                )
                for feature_index in range(len(self.FEATURE_NAMES)):
                    weights[class_index][feature_index] -= (
                        learning_rate
                        * grad_w[class_index][feature_index]
                        / count
                    )

        best_temperature = 1.0
        best_log_loss = float("inf")
        for temperature in (0.75, 0.9, 1.0, 1.1, 1.25, 1.5):
            metrics = self._evaluate(
                validation_rows,
                means,
                scales,
                weights,
                biases,
                temperature,
            )
            if metrics["log_loss"] < best_log_loss:
                best_log_loss = metrics["log_loss"]
                best_temperature = temperature

        final_metrics = self._evaluate(
            validation_rows,
            means,
            scales,
            weights,
            biases,
            best_temperature,
        )

        return RollingModel(
            model_id=model_id,
            competition=competition,
            feature_names=self.FEATURE_NAMES,
            means=tuple(means),
            scales=tuple(scales),
            weights=tuple(tuple(row) for row in weights),
            biases=tuple(biases),
            temperature=best_temperature,
            training_rows=len(train_rows),
            validation_rows=len(validation_rows),
            validation_accuracy=round(
                final_metrics["accuracy"], 2
            ),
            validation_log_loss=round(
                final_metrics["log_loss"], 4
            ),
            validation_brier_score=round(
                final_metrics["brier"], 4
            ),
            generated_at=int(
                now if now is not None else time.time()
            ),
        )

    def predict_from_features(
        self,
        *,
        model: RollingModel,
        features: tuple[float, ...],
    ) -> dict:
        scaled = self._scale(
            features,
            model.means,
            model.scales,
        )
        logits = [
            model.biases[class_index]
            + sum(
                weight * value
                for weight, value in zip(
                    model.weights[class_index],
                    scaled,
                )
            )
            for class_index in range(3)
        ]
        probabilities = self._temperature_probs(
            logits,
            model.temperature,
        )
        mapped = {
            outcome: probabilities[index]
            for index, outcome in enumerate(OUTCOMES)
        }
        return {
            "model_id": model.model_id,
            "home_probability": round(mapped["HOME"] * 100, 2),
            "draw_probability": round(mapped["DRAW"] * 100, 2),
            "away_probability": round(mapped["AWAY"] * 100, 2),
            "recommended_result": max(mapped, key=mapped.get),
        }

    def compare(
        self,
        *,
        report_id: str,
        rolling_model,
        ensemble_metrics: dict,
        now: int | None = None,
    ) -> ModelComparisonReport:
        rolling_rank = (
            rolling_model.validation_log_loss,
            rolling_model.validation_brier_score,
            -rolling_model.validation_accuracy,
        )
        ensemble_rank = (
            float(ensemble_metrics["log_loss"]),
            float(ensemble_metrics["brier"]),
            -float(ensemble_metrics["accuracy"]),
        )
        winner = (
            "ROLLING_LOGISTIC"
            if rolling_rank < ensemble_rank
            else "ENSEMBLE"
        )
        return ModelComparisonReport(
            report_id=report_id,
            competition=rolling_model.competition,
            rolling_accuracy=rolling_model.validation_accuracy,
            rolling_log_loss=rolling_model.validation_log_loss,
            rolling_brier=rolling_model.validation_brier_score,
            ensemble_accuracy=float(
                ensemble_metrics["accuracy"]
            ),
            ensemble_log_loss=float(
                ensemble_metrics["log_loss"]
            ),
            ensemble_brier=float(
                ensemble_metrics["brier"]
            ),
            winner=winner,
            generated_at=int(
                now if now is not None else time.time()
            ),
        )

    def _evaluate(
        self,
        rows,
        means,
        scales,
        weights,
        biases,
        temperature,
    ) -> dict:
        correct = 0
        log_losses = []
        briers = []
        for row in rows:
            scaled = self._scale(
                row.features,
                means,
                scales,
            )
            logits = [
                biases[class_index]
                + sum(
                    weight * value
                    for weight, value in zip(
                        weights[class_index],
                        scaled,
                    )
                )
                for class_index in range(3)
            ]
            probabilities = self._temperature_probs(
                logits,
                temperature,
            )
            target = OUTCOMES.index(row.label)
            predicted = max(
                range(3),
                key=lambda index: probabilities[index],
            )
            correct += predicted == target
            log_losses.append(
                -math.log(max(1e-9, probabilities[target]))
            )
            briers.append(
                sum(
                    (
                        probabilities[index]
                        - (1.0 if index == target else 0.0)
                    ) ** 2
                    for index in range(3)
                )
            )
        return {
            "accuracy": correct / len(rows) * 100,
            "log_loss": statistics.mean(log_losses),
            "brier": statistics.mean(briers),
        }

    @staticmethod
    def _fit_scaler(rows):
        columns = list(zip(*rows))
        means = [
            statistics.mean(column)
            for column in columns
        ]
        scales = []
        for column, mean in zip(columns, means):
            variance = statistics.mean(
                (value - mean) ** 2
                for value in column
            )
            scales.append(max(1e-6, math.sqrt(variance)))
        return means, scales

    @staticmethod
    def _scale(features, means, scales):
        return tuple(
            (value - mean) / scale
            for value, mean, scale in zip(
                features,
                means,
                scales,
            )
        )

    @staticmethod
    def _temperature_probs(logits, temperature):
        adjusted = [
            value / temperature
            for value in logits
        ]
        return RollingTeamModelService._softmax(adjusted)

    @staticmethod
    def _softmax(values):
        maximum = max(values)
        exps = [
            math.exp(value - maximum)
            for value in values
        ]
        total = sum(exps)
        return [
            value / total
            for value in exps
        ]

    @staticmethod
    def _append_history(
        history,
        *,
        team,
        goals_for,
        goals_against,
        xg_for,
        xg_against,
    ):
        points = (
            3 if goals_for > goals_against
            else 1 if goals_for == goals_against
            else 0
        )
        history.setdefault(team, []).append({
            "points": points,
            "goal_diff": goals_for - goals_against,
            "xg_diff": xg_for - xg_against,
        })

    @staticmethod
    def _rolling_stats(items):
        count = len(items)
        return {
            "points": sum(
                item["points"] for item in items
            ) / count / 3.0,
            "goal_diff": sum(
                item["goal_diff"] for item in items
            ) / count,
            "xg_diff": sum(
                item["xg_diff"] for item in items
            ) / count,
        }
