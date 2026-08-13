from __future__ import annotations

from .domain import OpponentDNA, WeaknessMap

class OpponentWeaknessAnalyzer:
    def analyze(self, dna: OpponentDNA) -> WeaknessMap:
        dna.validate()

        left_defense = min(
            1.0,
            dna.right_attack_share * 0.35
            + dna.defensive_line * 0.30
            + dna.build_up_risk * 0.35,
        )
        right_defense = min(
            1.0,
            dna.left_attack_share * 0.35
            + dna.defensive_line * 0.30
            + dna.build_up_risk * 0.35,
        )
        central_defense = min(
            1.0,
            dna.central_attack_share * 0.25
            + dna.defensive_line * 0.35
            + dna.build_up_risk * 0.40,
        )
        transition_defense = min(
            1.0,
            dna.pressing * 0.35
            + dna.defensive_line * 0.30
            + dna.transition_speed * 0.15
            + dna.build_up_risk * 0.20,
        )
        set_piece_defense = max(
            0.0,
            1.0 - dna.set_piece_threat * 0.55 - dna.defensive_line * 0.15,
        )
        pressure_resistance = max(
            0.0,
            1.0 - dna.build_up_risk * 0.60 - dna.directness * 0.20,
        )

        return WeaknessMap(
            left_defense=left_defense,
            right_defense=right_defense,
            central_defense=central_defense,
            transition_defense=transition_defense,
            set_piece_defense=set_piece_defense,
            pressure_resistance=pressure_resistance,
        )
