from __future__ import annotations

from dataclasses import dataclass
import json
import math
import statistics
import time

from .real_data_training import (
    BaselineModelReport,
    HistoricalMatch,
    RealDataTrainingService,
    RealDataValidationError,
)


@dataclass(frozen=True)
class EnsembleModel:
    model_id: str
    competition: str
    baseline: dict
    poisson_weight: float
    elo_form_weight: float
    calibration_temperature: float
    training_matches: int
    validation_matches: int
    validation_accuracy: float
    validation_log_loss: float
    validation_brier_score: float
    generated_at: int


@dataclass(frozen=True)
class WalkForwardEnsembleReport:
    report_id: str
    competition: str
    folds: int
    evaluated_matches: int
    accuracy: float
    mean_log_loss: float
    mean_brier_score: float
    mean_goal_error: float
    generated_at: int


class EnsembleTrainingService:
    def __init__(self):
        self.base = RealDataTrainingService()

    def train(
        self,
        *,
        model_id: str,
        csv_text: str,
        competition: str,
        validation_fraction: float = 0.25,
        now: int | None = None,
    ) -> EnsembleModel:
        matches, _ = self.base.parse_historical_csv(csv_text)
        selected = [
            item
            for item in matches
            if item.competition.lower() == competition.lower()
        ]
        if len(selected) < 20:
            raise RealDataValidationError(
                "Ensemble model için en az 20 geçerli maç gerekli"
            )

        split_index = max(
            14,
            int(len(selected) * (1.0 - validation_fraction)),
        )
        split_index = min(split_index, len(selected) - 5)
        train_matches = selected[:split_index]
        validation_matches = selected[split_index:]

        train_csv = self._to_csv(train_matches)
        baseline = self.base.train_baseline(
            model_id=f"{model_id}:baseline",
            csv_text=train_csv,
            competition=competition,
            validation_fraction=0.20,
            now=now,
        )

        candidates = (
            (0.55, 0.45),
            (0.65, 0.35),
            (0.75, 0.25),
            (0.85, 0.15),
        )
        temperatures = (0.85, 1.0, 1.15, 1.30)

        best = None
        for poisson_weight, elo_form_weight in candidates:
            for temperature in temperatures:
                metrics = self._evaluate(
                    validation_matches,
                    baseline,
                    poisson_weight,
                    elo_form_weight,
                    temperature,
                )
                ranking = (
                    metrics["log_loss"],
                    metrics["brier"],
                    -metrics["accuracy"],
                )
                if best is None or ranking < best["ranking"]:
                    best = {
                        "ranking": ranking,
                        "metrics": metrics,
                        "poisson_weight": poisson_weight,
                        "elo_form_weight": elo_form_weight,
                        "temperature": temperature,
                    }

        assert best is not None
        return EnsembleModel(
            model_id=model_id,
            competition=competition,
            baseline=baseline.__dict__,
            poisson_weight=best["poisson_weight"],
            elo_form_weight=best["elo_form_weight"],
            calibration_temperature=best["temperature"],
            training_matches=len(train_matches),
            validation_matches=len(validation_matches),
            validation_accuracy=round(best["metrics"]["accuracy"], 2),
            validation_log_loss=round(best["metrics"]["log_loss"], 4),
            validation_brier_score=round(best["metrics"]["brier"], 4),
            generated_at=int(now if now is not None else time.time()),
        )

    def predict(
        self,
        *,
        model: EnsembleModel,
        home_xg: float,
        away_xg: float,
        home_elo: float,
        away_elo: float,
        home_form: float = 0.5,
        away_form: float = 0.5,
    ) -> dict:
        baseline = BaselineModelReport(**model.baseline)
        base_prediction = self.base.predict_with_baseline(
            model=baseline,
            home_xg=home_xg,
            away_xg=away_xg,
            home_elo=home_elo,
            away_elo=away_elo,
        )
        poisson_probs = {
            "HOME": base_prediction["home_probability"] / 100,
            "DRAW": base_prediction["draw_probability"] / 100,
            "AWAY": base_prediction["away_probability"] / 100,
        }

        elo_delta = (home_elo - away_elo) / 400.0
        form_delta = home_form - away_form
        home_score = 0.55 + elo_delta * 0.30 + form_delta * 0.25
        away_score = 0.55 - elo_delta * 0.30 - form_delta * 0.25
        draw_score = 0.45 - abs(elo_delta) * 0.10 - abs(form_delta) * 0.10
        secondary = self._softmax({
            "HOME": home_score,
            "DRAW": draw_score,
            "AWAY": away_score,
        })

        combined = {
            outcome: (
                poisson_probs[outcome] * model.poisson_weight
                + secondary[outcome] * model.elo_form_weight
            )
            for outcome in ("HOME", "DRAW", "AWAY")
        }
        calibrated = self._temperature_scale(
            combined,
            model.calibration_temperature,
        )
        return {
            "model_id": model.model_id,
            "competition": model.competition,
            "expected_home_goals": base_prediction["expected_home_goals"],
            "expected_away_goals": base_prediction["expected_away_goals"],
            "home_probability": round(calibrated["HOME"] * 100, 2),
            "draw_probability": round(calibrated["DRAW"] * 100, 2),
            "away_probability": round(calibrated["AWAY"] * 100, 2),
            "predicted_score": base_prediction["predicted_score"],
            "recommended_result": max(
                calibrated,
                key=calibrated.get,
            ),
        }

    def walk_forward_backtest(
        self,
        *,
        report_id: str,
        csv_text: str,
        competition: str,
        minimum_train_size: int = 20,
        step_size: int = 5,
        now: int | None = None,
    ) -> WalkForwardEnsembleReport:
        matches, _ = self.base.parse_historical_csv(csv_text)
        selected = [
            item
            for item in matches
            if item.competition.lower() == competition.lower()
        ]
        if len(selected) < minimum_train_size + step_size:
            raise RealDataValidationError(
                "Walk-forward ensemble test için yeterli maç yok"
            )

        rows = []
        folds = 0
        start = minimum_train_size
        while start < len(selected):
            validation = selected[start:start + step_size]
            if not validation:
                break
            training = selected[:start]
            model = self.train(
                model_id=f"{report_id}:fold:{folds + 1}",
                csv_text=self._to_csv(training),
                competition=competition,
                validation_fraction=0.25,
                now=now,
            )
            for item in validation:
                prediction = self.predict(
                    model=model,
                    home_xg=item.home_xg,
                    away_xg=item.away_xg,
                    home_elo=item.home_elo,
                    away_elo=item.away_elo,
                )
                probs = {
                    "HOME": prediction["home_probability"] / 100,
                    "DRAW": prediction["draw_probability"] / 100,
                    "AWAY": prediction["away_probability"] / 100,
                }
                actual = self.base._result(
                    item.home_goals,
                    item.away_goals,
                )
                rows.append({
                    "correct": prediction["recommended_result"] == actual,
                    "log_loss": -math.log(max(1e-9, probs[actual])),
                    "brier": sum(
                        (
                            probs[outcome]
                            - (1.0 if outcome == actual else 0.0)
                        ) ** 2
                        for outcome in ("HOME", "DRAW", "AWAY")
                    ),
                    "goal_error": (
                        abs(
                            prediction["expected_home_goals"]
                            - item.home_goals
                        )
                        + abs(
                            prediction["expected_away_goals"]
                            - item.away_goals
                        )
                    ) / 2,
                })
            folds += 1
            start += step_size

        return WalkForwardEnsembleReport(
            report_id=report_id,
            competition=competition,
            folds=folds,
            evaluated_matches=len(rows),
            accuracy=round(
                sum(1 for row in rows if row["correct"])
                / len(rows) * 100,
                2,
            ),
            mean_log_loss=round(
                statistics.mean(row["log_loss"] for row in rows),
                4,
            ),
            mean_brier_score=round(
                statistics.mean(row["brier"] for row in rows),
                4,
            ),
            mean_goal_error=round(
                statistics.mean(row["goal_error"] for row in rows),
                4,
            ),
            generated_at=int(now if now is not None else time.time()),
        )

    def _evaluate(
        self,
        matches: list[HistoricalMatch],
        baseline: BaselineModelReport,
        poisson_weight: float,
        elo_form_weight: float,
        temperature: float,
    ) -> dict:
        correct = 0
        log_losses = []
        briers = []
        model = EnsembleModel(
            model_id="candidate",
            competition=baseline.competition,
            baseline=baseline.__dict__,
            poisson_weight=poisson_weight,
            elo_form_weight=elo_form_weight,
            calibration_temperature=temperature,
            training_matches=0,
            validation_matches=0,
            validation_accuracy=0,
            validation_log_loss=0,
            validation_brier_score=0,
            generated_at=0,
        )
        for item in matches:
            prediction = self.predict(
                model=model,
                home_xg=item.home_xg,
                away_xg=item.away_xg,
                home_elo=item.home_elo,
                away_elo=item.away_elo,
            )
            probs = {
                "HOME": prediction["home_probability"] / 100,
                "DRAW": prediction["draw_probability"] / 100,
                "AWAY": prediction["away_probability"] / 100,
            }
            actual = self.base._result(
                item.home_goals,
                item.away_goals,
            )
            correct += prediction["recommended_result"] == actual
            log_losses.append(
                -math.log(max(1e-9, probs[actual]))
            )
            briers.append(
                sum(
                    (
                        probs[outcome]
                        - (1.0 if outcome == actual else 0.0)
                    ) ** 2
                    for outcome in ("HOME", "DRAW", "AWAY")
                )
            )
        return {
            "accuracy": correct / len(matches) * 100,
            "log_loss": statistics.mean(log_losses),
            "brier": statistics.mean(briers),
        }

    @staticmethod
    def _temperature_scale(
        probabilities: dict,
        temperature: float,
    ) -> dict:
        logits = {
            key: math.log(max(1e-9, value)) / temperature
            for key, value in probabilities.items()
        }
        return EnsembleTrainingService._softmax(logits)

    @staticmethod
    def _softmax(scores: dict) -> dict:
        maximum = max(scores.values())
        exps = {
            key: math.exp(value - maximum)
            for key, value in scores.items()
        }
        total = sum(exps.values())
        return {
            key: value / total
            for key, value in exps.items()
        }

    @staticmethod
    def _to_csv(matches: list[HistoricalMatch]) -> str:
        columns = (
            "match_id",
            "competition",
            "season",
            "kickoff_at",
            "home_team",
            "away_team",
            "home_goals",
            "away_goals",
            "home_xg",
            "away_xg",
            "home_elo",
            "away_elo",
        )
        lines = [",".join(columns)]
        for item in matches:
            lines.append(
                ",".join(
                    str(getattr(item, column))
                    for column in columns
                )
            )
        return "\n".join(lines) + "\n"
