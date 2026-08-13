from dataclasses import dataclass

@dataclass(frozen=True)
class CrashRecoveryReport:
    recovered: bool
    last_sequence: int
    replayed_events: int
    used_snapshot: bool

class CrashRecoveryService:
    def __init__(self, replay_engine):
        self.replay_engine = replay_engine

    def recover(self, fixture_id, home_team_id, away_team_id):
        report = self.replay_engine.replay(
            fixture_id, home_team_id, away_team_id
        )
        return CrashRecoveryReport(
            True, report.state.last_sequence,
            report.replayed_events, report.used_snapshot
        )
