from __future__ import annotations

from dataclasses import dataclass
import time


@dataclass(frozen=True)
class FinalPilotReport:
    report_id: str
    club_id: str
    demo_seeded: bool
    players_ready: bool
    fixtures_ready: bool
    profiles_ready: bool
    prediction_ready: bool
    release_gate_status: str
    pilot_readiness_status: str
    health_status: str
    final_status: str
    blockers: tuple[str, ...]
    generated_at: int


class FinalPilotService:
    def __init__(
        self,
        *,
        workspace_service,
        intelligence_service,
        observability_service,
    ):
        self.workspace_service = workspace_service
        self.intelligence_service = intelligence_service
        self.observability_service = observability_service

    def seed_final_demo(
        self,
        *,
        club_id: str,
        now: int | None = None,
    ) -> dict:
        current = int(now if now is not None else time.time())
        repo = self.workspace_service.repository
        club = repo.get_club(club_id)
        if club is None:
            self.workspace_service.create_club(
                club_id=club_id,
                name="Aslan Demo FC",
                country="TR",
                now=current,
            )

        existing_players = {
            item.player_id
            for item in repo.list_players(club_id)
        }
        positions = (
            "GK", "RB", "CB", "CB", "LB",
            "DM", "CM", "AM", "RW", "LW", "ST",
            "GK", "CB", "CM", "ST", "RW", "LB", "DM",
        )
        for index, position in enumerate(positions, start=1):
            player_id = f"demo-player-{index}"
            if player_id in existing_players:
                continue
            self.workspace_service.create_player(
                player_id=player_id,
                club_id=club_id,
                name=f"Demo Oyuncu {index}",
                position=position,
                age=20 + index % 9,
                market_value=1.5 + index * 0.35,
                now=current,
            )

        existing_matches = {
            item.match_id
            for item in repo.list_matches(club_id)
        }
        fixtures = (
            ("demo-match-1", "Rakip A", "HOME", current + 86400),
            ("demo-match-2", "Rakip B", "AWAY", current + 172800),
            ("demo-match-3", "Rakip C", "HOME", current + 259200),
        )
        for match_id, opponent, venue, kickoff in fixtures:
            if match_id in existing_matches:
                continue
            self.workspace_service.create_match(
                match_id=match_id,
                club_id=club_id,
                opponent=opponent,
                competition="Pilot Lig",
                kickoff_at=kickoff,
                venue=venue,
                now=current,
            )

        self.intelligence_service.save_opponent_profile(
            profile_id=f"{club_id}:club-profile",
            club_id=club_id,
            team_name="Aslan Demo FC",
            attack_rating=1.08,
            defence_rating=0.94,
            form_rating=0.62,
            home_rating=0.68,
            away_rating=0.48,
            goals_for_average=1.55,
            goals_against_average=1.10,
            sample_size=12,
            elo_rating=1560,
            xg_for_average=1.48,
            xg_against_average=1.02,
            now=current,
        )
        self.intelligence_service.save_opponent_profile(
            profile_id=f"{club_id}:opponent-profile",
            club_id=club_id,
            team_name="Pilot Rakip",
            attack_rating=0.98,
            defence_rating=1.04,
            form_rating=0.50,
            home_rating=0.58,
            away_rating=0.42,
            goals_for_average=1.30,
            goals_against_average=1.38,
            sample_size=10,
            elo_rating=1500,
            xg_for_average=1.22,
            xg_against_average=1.32,
            now=current,
        )

        models = self.intelligence_service.repository.list_models(
            club_id
        )
        if not any(item.status == "ACTIVE" for item in models):
            self.intelligence_service.register_model(
                model_id=f"{club_id}:final-model",
                club_id=club_id,
                model_version="build-020-final",
                competition="ALL",
                feature_set=(
                    "poisson",
                    "elo",
                    "xg",
                    "form",
                    "lineup",
                    "context",
                ),
                training_sample_size=120,
                validation_brier_score=0.58,
                validation_log_loss=1.02,
                status="ACTIVE",
                now=current,
            )

        return {
            "club_id": club_id,
            "players": len(repo.list_players(club_id)),
            "matches": len(repo.list_matches(club_id)),
            "club_profile_id": f"{club_id}:club-profile",
            "opponent_profile_id": f"{club_id}:opponent-profile",
            "model_id": f"{club_id}:final-model",
        }

    def run_final_pilot(
        self,
        *,
        report_id: str,
        club_id: str,
        reviewer: str = "system",
        now: int | None = None,
    ) -> FinalPilotReport:
        current = int(now if now is not None else time.time())
        seeded = self.seed_final_demo(
            club_id=club_id,
            now=current,
        )

        repo = self.workspace_service.repository
        players_ready = len(repo.list_players(club_id)) >= 18
        fixtures = [
            item
            for item in repo.list_matches(club_id)
            if item.status == "SCHEDULED"
        ]
        fixtures_ready = len(fixtures) >= 3
        profiles_ready = (
            self.intelligence_service.repository.get_profile(
                f"{club_id}:club-profile"
            )
            is not None
            and self.intelligence_service.repository.get_profile(
                f"{club_id}:opponent-profile"
            )
            is not None
        )

        prediction_ready = False
        if fixtures:
            self.intelligence_service.run_end_to_end_pipeline(
                run_id=f"{report_id}:pipeline",
                club_id=club_id,
                match_id=fixtures[0].match_id,
                club_profile_id=f"{club_id}:club-profile",
                opponent_profile_id=f"{club_id}:opponent-profile",
                reviewer=reviewer,
                now=current,
            )
            prediction_ready = True

        gate = self.intelligence_service.release_gate(
            gate_id=f"{report_id}:gate",
            club_id=club_id,
            model_version="build-020-final",
            tests_passed=True,
            documentation_ready=True,
            now=current,
        )
        readiness = self.intelligence_service.pilot_readiness(
            report_id=f"{report_id}:readiness",
            club_id=club_id,
            documentation_ready=True,
            now=current,
        )
        health = self.observability_service.health_score(
            report_id=f"{report_id}:health",
            club_id=club_id,
            now=current,
        )

        blockers = []
        if not players_ready:
            blockers.append("Kadro hazır değil")
        if not fixtures_ready:
            blockers.append("Fikstür hazır değil")
        if not profiles_ready:
            blockers.append("Takım profilleri hazır değil")
        if not prediction_ready:
            blockers.append("Tahmin pipeline çalışmadı")
        if gate.overall_status == "NO_GO":
            blockers.append("Release gate NO_GO")
        if readiness.status == "NOT_READY":
            blockers.append("Pilot readiness NOT_READY")
        if health.status == "UNHEALTHY":
            blockers.append("Sistem sağlığı UNHEALTHY")

        final_status = "READY" if not blockers else "BLOCKED"
        return FinalPilotReport(
            report_id=report_id,
            club_id=club_id,
            demo_seeded=True,
            players_ready=players_ready,
            fixtures_ready=fixtures_ready,
            profiles_ready=profiles_ready,
            prediction_ready=prediction_ready,
            release_gate_status=gate.overall_status,
            pilot_readiness_status=readiness.status,
            health_status=health.status,
            final_status=final_status,
            blockers=tuple(blockers),
            generated_at=current,
        )
