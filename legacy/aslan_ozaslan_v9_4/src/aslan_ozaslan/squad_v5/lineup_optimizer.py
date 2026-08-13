from dataclasses import dataclass
from itertools import combinations
from .chemistry import SquadChemistryAnalyzer

@dataclass(frozen=True)
class LineupSelection:
    player_ids: tuple[str, ...]
    total_value: float
    chemistry_score: float
    fatigue_penalty: float
    objective_score: float

class LineupOptimizer:
    def optimize(self, *, players, requirements, chemistry_links):
        for p in players: p.validate()
        for r in requirements: r.validate()
        available = [p for p in players if p.available]
        if len(available) < sum(r.count for r in requirements):
            raise ValueError("Yeterli uygun oyuncu yok")
        groups = [[]]
        for req in requirements:
            candidates = [p for p in available if p.position == req.position]
            if len(candidates) < req.count:
                raise ValueError(f"{req.position} için yeterli oyuncu yok")
            next_groups = []
            for group in groups:
                used = {p.player_id for p in group}
                for choice in combinations(candidates, req.count):
                    if used.intersection(p.player_id for p in choice):
                        continue
                    next_groups.append(group + list(choice))
            groups = next_groups
        chemistry = SquadChemistryAnalyzer()
        best = None
        for group in groups:
            total_value = sum(p.value_score * (1 - p.fatigue * .35) for p in group)
            fatigue = sum(p.fatigue for p in group) / len(group)
            chem = chemistry.analyze([p.player_id for p in group], chemistry_links)
            objective = total_value * .78 + chem.chemistry_score * 20 - fatigue * 8
            current = LineupSelection(
                tuple(sorted(p.player_id for p in group)),
                total_value, chem.chemistry_score, fatigue, objective
            )
            if best is None or current.objective_score > best.objective_score:
                best = current
        return best
