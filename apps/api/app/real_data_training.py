from __future__ import annotations

from dataclasses import dataclass
import csv
import hashlib
import io
import json
import math
import statistics
import time


@dataclass(frozen=True)
class HistoricalMatch:
    match_id: str
    competition: str
    season: str
    kickoff_at: int
    home_team: str
    away_team: str
    home_goals: int
    away_goals: int
    home_xg: float
    away_xg: float
    home_elo: float
    away_elo: float


@dataclass(frozen=True)
class TrainingDatasetReport:
    report_id: str
    competition: str
    season: str
    total_rows: int
    valid_rows: int
    invalid_rows: int
    feature_names: tuple[str, ...]
    label_distribution: dict
    checksum: str
    generated_at: int


@dataclass(frozen=True)
class BaselineModelReport:
    model_id: str
    competition: str
    sample_size: int
    home_goal_rate: float
    away_goal_rate: float
    home_advantage: float
    elo_weight: float
    xg_weight: float
    validation_accuracy: float
    validation_brier_score: float
    generated_at: int


class RealDataValidationError(ValueError):
    pass


class RealDataTrainingService:
    REQUIRED_COLUMNS = (
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

    def parse_historical_csv(
        self,
        csv_text: str,
    ) -> tuple[tuple[HistoricalMatch, ...], tuple[dict, ...]]:
        reader = csv.DictReader(io.StringIO(csv_text))
        missing = [
            column
            for column in self.REQUIRED_COLUMNS
            if column not in (reader.fieldnames or [])
        ]
        if missing:
            raise RealDataValidationError(
                "Eksik kolonlar: " + ", ".join(missing)
            )

        valid = []
        issues = []
        seen_ids = set()

        for row_number, row in enumerate(reader, start=2):
            try:
                match_id = (row.get("match_id") or "").strip()
                if not match_id:
                    raise ValueError("match_id boş")
                if match_id in seen_ids:
                    raise ValueError("duplicate match_id")
                seen_ids.add(match_id)

                item = HistoricalMatch(
                    match_id=match_id,
                    competition=(row.get("competition") or "").strip(),
                    season=(row.get("season") or "").strip(),
                    kickoff_at=int(row["kickoff_at"]),
                    home_team=(row.get("home_team") or "").strip(),
                    away_team=(row.get("away_team") or "").strip(),
                    home_goals=int(row["home_goals"]),
                    away_goals=int(row["away_goals"]),
                    home_xg=float(row["home_xg"]),
                    away_xg=float(row["away_xg"]),
                    home_elo=float(row["home_elo"]),
                    away_elo=float(row["away_elo"]),
                )
                if not item.competition or not item.season:
                    raise ValueError("competition ve season zorunlu")
                if not item.home_team or not item.away_team:
                    raise ValueError("takım adları zorunlu")
                if min(
                    item.home_goals,
                    item.away_goals,
                    item.home_xg,
                    item.away_xg,
                ) < 0:
                    raise ValueError("gol ve xG negatif olamaz")
                if item.kickoff_at <= 0:
                    raise ValueError("kickoff_at pozitif olmalı")
                valid.append(item)
            except (ValueError, TypeError, KeyError) as exc:
                issues.append({
                    "row_number": row_number,
                    "message": str(exc),
                    "raw": dict(row),
                })

        valid.sort(key=lambda item: item.kickoff_at)
        return tuple(valid), tuple(issues)

    def dataset_report(
        self,
        *,
        report_id: str,
        csv_text: str,
        competition: str,
        season: str,
        now: int | None = None,
    ) -> TrainingDatasetReport:
        matches, issues = self.parse_historical_csv(csv_text)
        selected = [
            item
            for item in matches
            if item.competition.lower() == competition.lower()
            and item.season.lower() == season.lower()
        ]
        labels = {"HOME": 0, "DRAW": 0, "AWAY": 0}
        for item in selected:
            labels[self._result(item.home_goals, item.away_goals)] += 1

        canonical = json.dumps(
            [item.__dict__ for item in selected],
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        checksum = hashlib.sha256(
            canonical.encode("utf-8")
        ).hexdigest()
        return TrainingDatasetReport(
            report_id=report_id,
            competition=competition,
            season=season,
            total_rows=len(matches) + len(issues),
            valid_rows=len(selected),
            invalid_rows=len(issues),
            feature_names=(
                "home_xg",
                "away_xg",
                "elo_difference",
                "home_advantage",
            ),
            label_distribution=labels,
            checksum=checksum,
            generated_at=int(now if now is not None else time.time()),
        )

    def train_baseline(
        self,
        *,
        model_id: str,
        csv_text: str,
        competition: str,
        validation_fraction: float = 0.25,
        now: int | None = None,
    ) -> BaselineModelReport:
        if not 0.10 <= validation_fraction <= 0.40:
            raise RealDataValidationError(
                "validation_fraction 0.10 ile 0.40 arasında olmalıdır"
            )
        matches, issues = self.parse_historical_csv(csv_text)
        selected = [
            item
            for item in matches
            if item.competition.lower() == competition.lower()
        ]
        if len(selected) < 12:
            raise RealDataValidationError(
                "Model eğitimi için en az 12 geçerli maç gerekli"
            )

        split_index = max(
            8,
            int(len(selected) * (1.0 - validation_fraction)),
        )
        split_index = min(split_index, len(selected) - 3)
        train = selected[:split_index]
        validation = selected[split_index:]

        home_goal_rate = statistics.mean(
            item.home_goals for item in train
        )
        away_goal_rate = statistics.mean(
            item.away_goals for item in train
        )
        home_advantage = max(
            0.75,
            min(1.35, home_goal_rate / max(0.25, away_goal_rate)),
        )

        xg_error = statistics.mean(
            abs(item.home_xg - item.home_goals)
            + abs(item.away_xg - item.away_goals)
            for item in train
        ) / 2
        elo_signal = statistics.mean(
            abs(item.home_elo - item.away_elo)
            for item in train
        )
        xg_weight = max(0.35, min(0.80, 1.0 - xg_error / 4.0))
        elo_weight = max(0.05, min(0.30, elo_signal / 1000.0))

        correct = 0
        brier_values = []
        for item in validation:
            home_lambda, away_lambda = self._expected_goals(
                item=item,
                home_goal_rate=home_goal_rate,
                away_goal_rate=away_goal_rate,
                home_advantage=home_advantage,
                xg_weight=xg_weight,
                elo_weight=elo_weight,
            )
            probs = self._outcome_probabilities(
                home_lambda,
                away_lambda,
            )
            predicted = max(probs, key=probs.get)
            actual = self._result(
                item.home_goals,
                item.away_goals,
            )
            if predicted == actual:
                correct += 1
            brier_values.append(
                sum(
                    (
                        probs[result]
                        - (1.0 if result == actual else 0.0)
                    ) ** 2
                    for result in ("HOME", "DRAW", "AWAY")
                )
            )

        return BaselineModelReport(
            model_id=model_id,
            competition=competition,
            sample_size=len(selected),
            home_goal_rate=round(home_goal_rate, 4),
            away_goal_rate=round(away_goal_rate, 4),
            home_advantage=round(home_advantage, 4),
            elo_weight=round(elo_weight, 4),
            xg_weight=round(xg_weight, 4),
            validation_accuracy=round(
                correct / len(validation) * 100,
                2,
            ),
            validation_brier_score=round(
                statistics.mean(brier_values),
                4,
            ),
            generated_at=int(now if now is not None else time.time()),
        )

    def predict_with_baseline(
        self,
        *,
        model: BaselineModelReport,
        home_xg: float,
        away_xg: float,
        home_elo: float,
        away_elo: float,
    ) -> dict:
        item = HistoricalMatch(
            match_id="prediction",
            competition=model.competition,
            season="current",
            kickoff_at=1,
            home_team="home",
            away_team="away",
            home_goals=0,
            away_goals=0,
            home_xg=home_xg,
            away_xg=away_xg,
            home_elo=home_elo,
            away_elo=away_elo,
        )
        home_lambda, away_lambda = self._expected_goals(
            item=item,
            home_goal_rate=model.home_goal_rate,
            away_goal_rate=model.away_goal_rate,
            home_advantage=model.home_advantage,
            xg_weight=model.xg_weight,
            elo_weight=model.elo_weight,
        )
        probs = self._outcome_probabilities(
            home_lambda,
            away_lambda,
        )
        best_score = max(
            (
                (
                    home_goals,
                    away_goals,
                    self._poisson(home_goals, home_lambda)
                    * self._poisson(away_goals, away_lambda),
                )
                for home_goals in range(7)
                for away_goals in range(7)
            ),
            key=lambda item: item[2],
        )
        return {
            "expected_home_goals": round(home_lambda, 3),
            "expected_away_goals": round(away_lambda, 3),
            "home_probability": round(probs["HOME"] * 100, 2),
            "draw_probability": round(probs["DRAW"] * 100, 2),
            "away_probability": round(probs["AWAY"] * 100, 2),
            "predicted_score": f"{best_score[0]}-{best_score[1]}",
        }

    @staticmethod
    def _expected_goals(
        *,
        item: HistoricalMatch,
        home_goal_rate: float,
        away_goal_rate: float,
        home_advantage: float,
        xg_weight: float,
        elo_weight: float,
    ) -> tuple[float, float]:
        elo_delta = (item.home_elo - item.away_elo) / 400.0
        home_base = (
            home_goal_rate * (1.0 - xg_weight)
            + item.home_xg * xg_weight
        )
        away_base = (
            away_goal_rate * (1.0 - xg_weight)
            + item.away_xg * xg_weight
        )
        home_lambda = home_base * home_advantage * (
            1.0 + elo_delta * elo_weight
        )
        away_lambda = away_base / max(0.75, home_advantage) * (
            1.0 - elo_delta * elo_weight
        )
        return (
            max(0.15, min(4.5, home_lambda)),
            max(0.15, min(4.5, away_lambda)),
        )

    @classmethod
    def _outcome_probabilities(
        cls,
        home_lambda: float,
        away_lambda: float,
    ) -> dict:
        home = 0.0
        draw = 0.0
        away = 0.0
        for home_goals in range(10):
            for away_goals in range(10):
                probability = (
                    cls._poisson(home_goals, home_lambda)
                    * cls._poisson(away_goals, away_lambda)
                )
                if home_goals > away_goals:
                    home += probability
                elif home_goals == away_goals:
                    draw += probability
                else:
                    away += probability
        total = home + draw + away
        return {
            "HOME": home / total,
            "DRAW": draw / total,
            "AWAY": away / total,
        }

    @staticmethod
    def _poisson(goals: int, expected: float) -> float:
        return (
            math.exp(-expected)
            * expected ** goals
            / math.factorial(goals)
        )

    @staticmethod
    def _result(home_goals: int, away_goals: int) -> str:
        if home_goals > away_goals:
            return "HOME"
        if home_goals < away_goals:
            return "AWAY"
        return "DRAW"
