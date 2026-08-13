from dataclasses import dataclass

@dataclass(frozen=True)
class ReplayVerificationReport:
    valid: bool
    mismatches: tuple[str, ...]

class ReplayVerifier:
    def verify(self, reconstructed, expected):
        fields = (
            "last_sequence","minute","home_goals","away_goals",
            "home_red_cards","away_red_cards","processed_events"
        )
        mismatches = tuple(
            field for field in fields
            if getattr(reconstructed, field) != getattr(expected, field)
        )
        return ReplayVerificationReport(not mismatches, mismatches)
