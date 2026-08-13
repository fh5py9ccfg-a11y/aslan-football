from dataclasses import dataclass
from itertools import combinations

@dataclass(frozen=True)
class ChemistryLink:
    player_a: str
    player_b: str
    compatibility: float

    def validate(self):
        if self.player_a == self.player_b or not 0 <= self.compatibility <= 1:
            raise ValueError("Geçersiz chemistry link")

@dataclass(frozen=True)
class ChemistryReport:
    average_compatibility: float
    linked_pairs: int
    missing_pairs: int
    chemistry_score: float

class SquadChemistryAnalyzer:
    def analyze(self, player_ids, links):
        if len(set(player_ids)) != len(player_ids):
            raise ValueError("Oyuncu kimlikleri benzersiz olmalıdır")
        if len(player_ids) < 2:
            return ChemistryReport(1, 0, 0, 1)
        link_map = {}
        for link in links:
            link.validate()
            link_map[tuple(sorted((link.player_a, link.player_b)))] = link.compatibility
        total = linked = missing = 0
        for a, b in combinations(player_ids, 2):
            key = tuple(sorted((a, b)))
            if key in link_map:
                total += link_map[key]; linked += 1
            else:
                total += .5; missing += 1
        pairs = linked + missing
        avg = total / pairs
        coverage = linked / pairs
        return ChemistryReport(avg, linked, missing, avg * .8 + coverage * .2)
