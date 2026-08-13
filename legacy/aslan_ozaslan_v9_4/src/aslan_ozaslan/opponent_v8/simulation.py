from __future__ import annotations
from dataclasses import dataclass
import random

@dataclass(frozen=True)
class OpponentSimulationReport:
    iterations: int
    expected_goals_for: float
    expected_goals_against: float
    first_goal_probability: float
    transition_break_probability: float
    set_piece_goal_probability: float

class OpponentScenarioSimulator:
    def simulate(
        self,
        *,
        attack_strength: float,
        defense_strength: float,
        opponent_transition_threat: float,
        opponent_set_piece_threat: float,
        iterations: int = 5000,
        seed: int = 1,
    ) -> OpponentSimulationReport:
        if iterations <= 0:
            raise ValueError("iterations pozitif olmalıdır")
        for value in (
            attack_strength,
            defense_strength,
            opponent_transition_threat,
            opponent_set_piece_threat,
        ):
            if not 0 <= value <= 1:
                raise ValueError("Simülasyon girdileri geçersiz")

        rng = random.Random(seed)
        goals_for = 0.0
        goals_against = 0.0
        first_goal = 0
        transition_break = 0
        set_piece_goal = 0

        for _ in range(iterations):
            gf = max(0.0, rng.gauss(attack_strength * 2.0, 0.45))
            ga = max(
                0.0,
                rng.gauss(
                    (1.0 - defense_strength) * 1.4
                    + opponent_transition_threat * 0.6,
                    0.40,
                ),
            )
            goals_for += gf
            goals_against += ga
            first_goal += int(gf > ga)
            transition_break += int(
                rng.random() < opponent_transition_threat * 0.55
            )
            set_piece_goal += int(
                rng.random() < opponent_set_piece_threat * 0.18
            )

        return OpponentSimulationReport(
            iterations=iterations,
            expected_goals_for=goals_for / iterations,
            expected_goals_against=goals_against / iterations,
            first_goal_probability=first_goal / iterations,
            transition_break_probability=transition_break / iterations,
            set_piece_goal_probability=set_piece_goal / iterations,
        )
