from __future__ import annotations
from math import exp, factorial

class PoissonSampler:
    def probability(self, goals: int, expected_goals: float) -> float:
        if goals < 0 or expected_goals < 0:
            raise ValueError("Poisson girdileri negatif olamaz")
        return exp(-expected_goals) * (expected_goals ** goals) / factorial(goals)

    def sample(self, expected_goals: float, rng) -> int:
        if expected_goals < 0:
            raise ValueError("expected_goals negatif olamaz")
        threshold = exp(-expected_goals)
        product = 1.0
        count = 0
        while product > threshold:
            count += 1
            product *= rng.random()
        return count - 1
