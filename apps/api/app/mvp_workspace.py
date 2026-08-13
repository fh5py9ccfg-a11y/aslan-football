from __future__ import annotations

from dataclasses import dataclass
import json
import time


@dataclass(frozen=True)
class Club:
    club_id: str
    name: str
    country: str
    created_at: int


@dataclass(frozen=True)
class Player:
    player_id: str
    club_id: str
    name: str
    position: str
    age: int
    market_value: float
    availability: str = "AVAILABLE"
    availability_note: str = ""
    created_at: int = 0


@dataclass(frozen=True)
class Match:
    match_id: str
    club_id: str
    opponent: str
    competition: str
    kickoff_at: int
    venue: str
    status: str
    goals_for: int | None
    goals_against: int | None
    created_at: int


@dataclass(frozen=True)
class TrainingSession:
    session_id: str
    club_id: str
    title: str
    starts_at: int
    focus: str
    created_at: int


@dataclass(frozen=True)
class TrainingAttendance:
    session_id: str
    player_id: str
    status: str
    note: str
    recorded_at: int


@dataclass(frozen=True)
class MatchSquad:
    match_id: str
    club_id: str
    player_ids: tuple[str, ...]
    updated_at: int


@dataclass(frozen=True)
class PlayerMatchPerformance:
    match_id: str
    club_id: str
    player_id: str
    minutes: int
    goals: int
    assists: int
    rating: float
    note: str
    recorded_at: int


@dataclass(frozen=True)
class MatchReport:
    match_id: str
    club_id: str
    summary: str
    positives: str
    improvements: str
    created_at: int


@dataclass(frozen=True)
class OpponentProfile:
    opponent_id: str
    club_id: str
    name: str
    formation: str
    strengths: tuple[str, ...]
    weaknesses: tuple[str, ...]
    key_players: tuple[str, ...]
    notes: str
    updated_at: int


@dataclass(frozen=True)
class MatchPreparation:
    preparation_id: str
    match_id: str
    club_id: str
    opponent_id: str
    tactical_plan: str
    pressing_plan: str
    set_piece_plan: str
    objectives: tuple[str, ...]
    status: str
    created_at: int
    updated_at: int


class MVPValidationError(ValueError):
    pass


class RedisMVPRepository:
    def __init__(
        self,
        client,
        *,
        prefix: str = "aslan:mvp",
        ttl_seconds: int = 31_536_000,
    ):
        self.client = client
        self.prefix = prefix
        self.ttl_seconds = ttl_seconds

    def save_club(self, item: Club) -> Club:
        self.client.setex(
            self._club_key(item.club_id),
            self.ttl_seconds,
            json.dumps(item.__dict__, ensure_ascii=False),
        )
        self.client.sadd(self._club_index(), item.club_id)
        return item

    def get_club(self, club_id: str) -> Club | None:
        payload = self.client.get(self._club_key(club_id))
        if payload is None:
            return None
        if isinstance(payload, bytes):
            payload = payload.decode("utf-8")
        return Club(**json.loads(payload))

    def list_clubs(self) -> tuple[Club, ...]:
        items = []
        for club_id in self.client.smembers(self._club_index()):
            if isinstance(club_id, bytes):
                club_id = club_id.decode("utf-8")
            item = self.get_club(str(club_id))
            if item:
                items.append(item)
        items.sort(key=lambda item: item.name.lower())
        return tuple(items)

    def save_player(self, item: Player) -> Player:
        self.client.setex(
            self._player_key(item.player_id),
            self.ttl_seconds,
            json.dumps(item.__dict__, ensure_ascii=False),
        )
        self.client.sadd(
            self._club_player_index(item.club_id),
            item.player_id,
        )
        return item

    def list_players(self, club_id: str) -> tuple[Player, ...]:
        items = []
        for player_id in self.client.smembers(
            self._club_player_index(club_id)
        ):
            if isinstance(player_id, bytes):
                player_id = player_id.decode("utf-8")
            payload = self.client.get(
                self._player_key(str(player_id))
            )
            if payload is None:
                continue
            if isinstance(payload, bytes):
                payload = payload.decode("utf-8")
            items.append(Player(**json.loads(payload)))
        items.sort(key=lambda item: item.name.lower())
        return tuple(items)

    def get_player(
        self,
        *,
        club_id: str,
        player_id: str,
    ) -> Player | None:
        for item in self.list_players(club_id):
            if item.player_id == player_id:
                return item
        return None

    def delete_player(
        self,
        *,
        club_id: str,
        player_id: str,
    ) -> bool:
        key = self._player_key(player_id)
        existed = self.client.get(key) is not None
        if hasattr(self.client, "delete"):
            self.client.delete(key)
        else:
            self.client.values.pop(key, None)
        if hasattr(self.client, "srem"):
            self.client.srem(
                self._club_player_index(club_id),
                player_id,
            )
        else:
            self.client.sets.setdefault(
                self._club_player_index(club_id),
                set(),
            ).discard(player_id)
        return existed

    def save_match(self, item: Match) -> Match:
        self.client.setex(
            self._match_key(item.match_id),
            self.ttl_seconds,
            json.dumps(item.__dict__, ensure_ascii=False),
        )
        self.client.sadd(
            self._club_match_index(item.club_id),
            item.match_id,
        )
        return item

    def list_matches(self, club_id: str) -> tuple[Match, ...]:
        items = []
        for match_id in self.client.smembers(
            self._club_match_index(club_id)
        ):
            if isinstance(match_id, bytes):
                match_id = match_id.decode("utf-8")
            payload = self.client.get(
                self._match_key(str(match_id))
            )
            if payload is None:
                continue
            if isinstance(payload, bytes):
                payload = payload.decode("utf-8")
            items.append(Match(**json.loads(payload)))
        items.sort(key=lambda item: item.kickoff_at, reverse=True)
        return tuple(items)


    def save_training(
        self,
        item: TrainingSession,
    ) -> TrainingSession:
        self.client.setex(
            self._training_key(item.session_id),
            self.ttl_seconds,
            json.dumps(
                item.__dict__,
                ensure_ascii=False,
            ),
        )
        self.client.sadd(
            self._club_training_index(item.club_id),
            item.session_id,
        )
        return item

    def get_training(
        self,
        session_id: str,
    ) -> TrainingSession | None:
        payload = self.client.get(
            self._training_key(session_id)
        )
        if payload is None:
            return None
        if isinstance(payload, bytes):
            payload = payload.decode("utf-8")
        return TrainingSession(**json.loads(payload))

    def list_trainings(
        self,
        club_id: str,
    ) -> tuple[TrainingSession, ...]:
        items = []
        for session_id in self.client.smembers(
            self._club_training_index(club_id)
        ):
            if isinstance(session_id, bytes):
                session_id = session_id.decode("utf-8")
            item = self.get_training(str(session_id))
            if item is not None:
                items.append(item)
        items.sort(
            key=lambda item: item.starts_at,
            reverse=True,
        )
        return tuple(items)

    def save_attendance(
        self,
        item: TrainingAttendance,
    ) -> TrainingAttendance:
        self.client.setex(
            self._attendance_key(
                item.session_id,
                item.player_id,
            ),
            self.ttl_seconds,
            json.dumps(
                item.__dict__,
                ensure_ascii=False,
            ),
        )
        self.client.sadd(
            self._attendance_index(item.session_id),
            item.player_id,
        )
        return item

    def list_attendance(
        self,
        session_id: str,
    ) -> tuple[TrainingAttendance, ...]:
        items = []
        for player_id in self.client.smembers(
            self._attendance_index(session_id)
        ):
            if isinstance(player_id, bytes):
                player_id = player_id.decode("utf-8")
            payload = self.client.get(
                self._attendance_key(
                    session_id,
                    str(player_id),
                )
            )
            if payload is None:
                continue
            if isinstance(payload, bytes):
                payload = payload.decode("utf-8")
            items.append(
                TrainingAttendance(**json.loads(payload))
            )
        items.sort(key=lambda item: item.player_id)
        return tuple(items)

    def save_squad(
        self,
        item: MatchSquad,
    ) -> MatchSquad:
        payload = {
            **item.__dict__,
            "player_ids": list(item.player_ids),
        }
        self.client.setex(
            self._squad_key(item.match_id),
            self.ttl_seconds,
            json.dumps(
                payload,
                ensure_ascii=False,
            ),
        )
        return item

    def get_squad(
        self,
        match_id: str,
    ) -> MatchSquad | None:
        payload = self.client.get(
            self._squad_key(match_id)
        )
        if payload is None:
            return None
        if isinstance(payload, bytes):
            payload = payload.decode("utf-8")
        data = json.loads(payload)
        data["player_ids"] = tuple(
            data["player_ids"]
        )
        return MatchSquad(**data)


    def save_performance(
        self,
        item: PlayerMatchPerformance,
    ) -> PlayerMatchPerformance:
        self.client.setex(
            self._performance_key(
                item.match_id,
                item.player_id,
            ),
            self.ttl_seconds,
            json.dumps(
                item.__dict__,
                ensure_ascii=False,
            ),
        )
        self.client.sadd(
            self._match_performance_index(
                item.match_id
            ),
            item.player_id,
        )
        return item

    def list_performances(
        self,
        match_id: str,
    ) -> tuple[PlayerMatchPerformance, ...]:
        items = []
        for player_id in self.client.smembers(
            self._match_performance_index(
                match_id
            )
        ):
            if isinstance(player_id, bytes):
                player_id = player_id.decode("utf-8")
            payload = self.client.get(
                self._performance_key(
                    match_id,
                    str(player_id),
                )
            )
            if payload is None:
                continue
            if isinstance(payload, bytes):
                payload = payload.decode("utf-8")
            items.append(
                PlayerMatchPerformance(
                    **json.loads(payload)
                )
            )
        items.sort(
            key=lambda item: (
                item.rating,
                item.goals,
                item.assists,
            ),
            reverse=True,
        )
        return tuple(items)

    def save_match_report(
        self,
        item: MatchReport,
    ) -> MatchReport:
        self.client.setex(
            self._match_report_key(
                item.match_id
            ),
            self.ttl_seconds,
            json.dumps(
                item.__dict__,
                ensure_ascii=False,
            ),
        )
        return item

    def get_match_report(
        self,
        match_id: str,
    ) -> MatchReport | None:
        payload = self.client.get(
            self._match_report_key(match_id)
        )
        if payload is None:
            return None
        if isinstance(payload, bytes):
            payload = payload.decode("utf-8")
        return MatchReport(**json.loads(payload))


    def save_opponent(
        self,
        item: OpponentProfile,
    ) -> OpponentProfile:
        payload = {
            **item.__dict__,
            "strengths": list(item.strengths),
            "weaknesses": list(item.weaknesses),
            "key_players": list(item.key_players),
        }
        self.client.setex(
            self._opponent_key(
                item.club_id,
                item.opponent_id,
            ),
            self.ttl_seconds,
            json.dumps(
                payload,
                ensure_ascii=False,
            ),
        )
        self.client.sadd(
            self._opponent_index(item.club_id),
            item.opponent_id,
        )
        return item

    def get_opponent(
        self,
        *,
        club_id: str,
        opponent_id: str,
    ) -> OpponentProfile | None:
        payload = self.client.get(
            self._opponent_key(
                club_id,
                opponent_id,
            )
        )
        if payload is None:
            return None
        if isinstance(payload, bytes):
            payload = payload.decode("utf-8")
        data = json.loads(payload)
        data["strengths"] = tuple(data["strengths"])
        data["weaknesses"] = tuple(data["weaknesses"])
        data["key_players"] = tuple(
            data["key_players"]
        )
        return OpponentProfile(**data)

    def list_opponents(
        self,
        club_id: str,
    ) -> tuple[OpponentProfile, ...]:
        items = []
        for opponent_id in self.client.smembers(
            self._opponent_index(club_id)
        ):
            if isinstance(opponent_id, bytes):
                opponent_id = opponent_id.decode(
                    "utf-8"
                )
            item = self.get_opponent(
                club_id=club_id,
                opponent_id=str(opponent_id),
            )
            if item is not None:
                items.append(item)
        items.sort(key=lambda item: item.name.lower())
        return tuple(items)

    def save_preparation(
        self,
        item: MatchPreparation,
    ) -> MatchPreparation:
        payload = {
            **item.__dict__,
            "objectives": list(item.objectives),
        }
        self.client.setex(
            self._preparation_key(
                item.preparation_id
            ),
            self.ttl_seconds,
            json.dumps(
                payload,
                ensure_ascii=False,
            ),
        )
        self.client.sadd(
            self._match_preparation_index(
                item.match_id
            ),
            item.preparation_id,
        )
        return item

    def get_preparation(
        self,
        preparation_id: str,
    ) -> MatchPreparation | None:
        payload = self.client.get(
            self._preparation_key(
                preparation_id
            )
        )
        if payload is None:
            return None
        if isinstance(payload, bytes):
            payload = payload.decode("utf-8")
        data = json.loads(payload)
        data["objectives"] = tuple(
            data["objectives"]
        )
        return MatchPreparation(**data)

    def list_preparations(
        self,
        match_id: str,
    ) -> tuple[MatchPreparation, ...]:
        items = []
        for preparation_id in self.client.smembers(
            self._match_preparation_index(
                match_id
            )
        ):
            if isinstance(preparation_id, bytes):
                preparation_id = preparation_id.decode(
                    "utf-8"
                )
            item = self.get_preparation(
                str(preparation_id)
            )
            if item is not None:
                items.append(item)
        items.sort(
            key=lambda item: item.updated_at,
            reverse=True,
        )
        return tuple(items)

    def _club_key(self, item_id: str) -> str:
        return f"{self.prefix}:club:{item_id}"

    def _club_index(self) -> str:
        return f"{self.prefix}:clubs"

    def _player_key(self, item_id: str) -> str:
        return f"{self.prefix}:player:{item_id}"

    def _club_player_index(self, club_id: str) -> str:
        return f"{self.prefix}:players:{club_id}"

    def _match_key(self, item_id: str) -> str:
        return f"{self.prefix}:match:{item_id}"

    def _club_match_index(self, club_id: str) -> str:
        return f"{self.prefix}:matches:{club_id}"

    def _training_key(self, session_id: str) -> str:
        return f"{self.prefix}:training:{session_id}"

    def _club_training_index(self, club_id: str) -> str:
        return f"{self.prefix}:trainings:{club_id}"

    def _attendance_key(
        self,
        session_id: str,
        player_id: str,
    ) -> str:
        return (
            f"{self.prefix}:attendance:"
            f"{session_id}:{player_id}"
        )

    def _attendance_index(self, session_id: str) -> str:
        return f"{self.prefix}:attendance-index:{session_id}"

    def _squad_key(self, match_id: str) -> str:
        return f"{self.prefix}:squad:{match_id}"

    def _performance_key(
        self,
        match_id: str,
        player_id: str,
    ) -> str:
        return (
            f"{self.prefix}:performance:"
            f"{match_id}:{player_id}"
        )

    def _match_performance_index(
        self,
        match_id: str,
    ) -> str:
        return (
            f"{self.prefix}:performances:"
            f"{match_id}"
        )

    def _match_report_key(
        self,
        match_id: str,
    ) -> str:
        return (
            f"{self.prefix}:match-report:"
            f"{match_id}"
        )

    def _opponent_key(
        self,
        club_id: str,
        opponent_id: str,
    ) -> str:
        return (
            f"{self.prefix}:opponent:"
            f"{club_id}:{opponent_id}"
        )

    def _opponent_index(
        self,
        club_id: str,
    ) -> str:
        return (
            f"{self.prefix}:opponents:"
            f"{club_id}"
        )

    def _preparation_key(
        self,
        preparation_id: str,
    ) -> str:
        return (
            f"{self.prefix}:preparation:"
            f"{preparation_id}"
        )

    def _match_preparation_index(
        self,
        match_id: str,
    ) -> str:
        return (
            f"{self.prefix}:preparations:"
            f"{match_id}"
        )


class MVPWorkspaceService:
    def __init__(self, *, repository):
        self.repository = repository

    def create_club(
        self,
        *,
        club_id: str,
        name: str,
        country: str,
        now: int | None = None,
    ) -> Club:
        if len(name.strip()) < 2:
            raise MVPValidationError("Kulüp adı çok kısa")
        item = Club(
            club_id=club_id,
            name=name.strip(),
            country=country.strip(),
            created_at=int(now if now is not None else time.time()),
        )
        return self.repository.save_club(item)

    def create_player(
        self,
        *,
        player_id: str,
        club_id: str,
        name: str,
        position: str,
        age: int,
        market_value: float,
        now: int | None = None,
    ) -> Player:
        if self.repository.get_club(club_id) is None:
            raise KeyError("Kulüp bulunamadı")
        if not 14 <= age <= 50:
            raise MVPValidationError("Oyuncu yaşı 14 ile 50 arasında olmalıdır")
        if market_value < 0:
            raise MVPValidationError("Piyasa değeri negatif olamaz")
        item = Player(
            player_id=player_id,
            club_id=club_id,
            name=name.strip(),
            position=position.strip().upper(),
            age=age,
            market_value=market_value,
            created_at=int(now if now is not None else time.time()),
        )
        return self.repository.save_player(item)


    def update_player(
        self,
        *,
        player_id: str,
        club_id: str,
        name: str,
        position: str,
        age: int,
        market_value: float,
    ) -> Player:
        current = self.repository.get_player(
            club_id=club_id,
            player_id=player_id,
        )
        if current is None:
            raise KeyError("Oyuncu bulunamadı")
        if not 14 <= age <= 50:
            raise MVPValidationError(
                "Oyuncu yaşı 14 ile 50 arasında olmalıdır"
            )
        if market_value < 0:
            raise MVPValidationError(
                "Piyasa değeri negatif olamaz"
            )
        updated = Player(
            **{
                **current.__dict__,
                "name": name.strip(),
                "position": position.strip().upper(),
                "age": age,
                "market_value": market_value,
            }
        )
        return self.repository.save_player(updated)

    def delete_player(
        self,
        *,
        player_id: str,
        club_id: str,
    ) -> None:
        if not self.repository.delete_player(
            club_id=club_id,
            player_id=player_id,
        ):
            raise KeyError("Oyuncu bulunamadı")

    def create_match(
        self,
        *,
        match_id: str,
        club_id: str,
        opponent: str,
        competition: str,
        kickoff_at: int,
        venue: str,
        now: int | None = None,
    ) -> Match:
        if self.repository.get_club(club_id) is None:
            raise KeyError("Kulüp bulunamadı")
        item = Match(
            match_id=match_id,
            club_id=club_id,
            opponent=opponent.strip(),
            competition=competition.strip(),
            kickoff_at=kickoff_at,
            venue=venue.strip().upper(),
            status="SCHEDULED",
            goals_for=None,
            goals_against=None,
            created_at=int(now if now is not None else time.time()),
        )
        return self.repository.save_match(item)

    def complete_match(
        self,
        *,
        match_id: str,
        club_id: str,
        goals_for: int,
        goals_against: int,
    ) -> Match:
        current = next(
            (
                item
                for item in self.repository.list_matches(club_id)
                if item.match_id == match_id
            ),
            None,
        )
        if current is None:
            raise KeyError("Maç bulunamadı")
        if goals_for < 0 or goals_against < 0:
            raise MVPValidationError("Gol sayıları negatif olamaz")
        updated = Match(
            **{
                **current.__dict__,
                "status": "COMPLETED",
                "goals_for": goals_for,
                "goals_against": goals_against,
            }
        )
        return self.repository.save_match(updated)



    def set_player_availability(
        self,
        *,
        club_id: str,
        player_id: str,
        availability: str,
        note: str = "",
    ) -> Player:
        current = self.repository.get_player(
            club_id=club_id,
            player_id=player_id,
        )
        if current is None:
            raise KeyError("Oyuncu bulunamadı")
        normalized = availability.upper()
        if normalized not in {
            "AVAILABLE",
            "INJURED",
            "SUSPENDED",
            "DOUBTFUL",
            "REST",
        }:
            raise MVPValidationError(
                "Geçersiz oyuncu uygunluk durumu"
            )
        updated = Player(
            **{
                **current.__dict__,
                "availability": normalized,
                "availability_note": note.strip(),
            }
        )
        return self.repository.save_player(updated)

    def create_training(
        self,
        *,
        session_id: str,
        club_id: str,
        title: str,
        starts_at: int,
        focus: str,
        now: int | None = None,
    ) -> TrainingSession:
        if self.repository.get_club(club_id) is None:
            raise KeyError("Kulüp bulunamadı")
        if len(title.strip()) < 3:
            raise MVPValidationError(
                "Antrenman başlığı çok kısa"
            )
        item = TrainingSession(
            session_id=session_id,
            club_id=club_id,
            title=title.strip(),
            starts_at=starts_at,
            focus=focus.strip(),
            created_at=int(
                now if now is not None
                else time.time()
            ),
        )
        return self.repository.save_training(item)

    def record_attendance(
        self,
        *,
        session_id: str,
        player_id: str,
        status: str,
        note: str = "",
        now: int | None = None,
    ) -> TrainingAttendance:
        session = self.repository.get_training(
            session_id
        )
        if session is None:
            raise KeyError("Antrenman bulunamadı")
        player = self.repository.get_player(
            club_id=session.club_id,
            player_id=player_id,
        )
        if player is None:
            raise KeyError("Oyuncu bulunamadı")
        normalized = status.upper()
        if normalized not in {
            "PRESENT",
            "ABSENT",
            "LIMITED",
            "EXCUSED",
        }:
            raise MVPValidationError(
                "Geçersiz katılım durumu"
            )
        item = TrainingAttendance(
            session_id=session_id,
            player_id=player_id,
            status=normalized,
            note=note.strip(),
            recorded_at=int(
                now if now is not None
                else time.time()
            ),
        )
        return self.repository.save_attendance(item)

    def set_match_squad(
        self,
        *,
        match_id: str,
        club_id: str,
        player_ids: tuple[str, ...],
        now: int | None = None,
    ) -> MatchSquad:
        match = next(
            (
                item
                for item in self.repository.list_matches(
                    club_id
                )
                if item.match_id == match_id
            ),
            None,
        )
        if match is None:
            raise KeyError("Maç bulunamadı")
        unique_ids = tuple(dict.fromkeys(player_ids))
        players = {
            item.player_id: item
            for item in self.repository.list_players(
                club_id
            )
        }
        missing = [
            player_id
            for player_id in unique_ids
            if player_id not in players
        ]
        if missing:
            raise KeyError(
                "Kadroda bulunamayan oyuncu: "
                + ", ".join(missing)
            )
        blocked = [
            player_id
            for player_id in unique_ids
            if players[player_id].availability
            in {"INJURED", "SUSPENDED"}
        ]
        if blocked:
            raise MVPValidationError(
                "Kadroya uygun olmayan oyuncu: "
                + ", ".join(blocked)
            )
        item = MatchSquad(
            match_id=match_id,
            club_id=club_id,
            player_ids=unique_ids,
            updated_at=int(
                now if now is not None
                else time.time()
            ),
        )
        return self.repository.save_squad(item)


    def record_player_performance(
        self,
        *,
        match_id: str,
        club_id: str,
        player_id: str,
        minutes: int,
        goals: int,
        assists: int,
        rating: float,
        note: str = "",
        now: int | None = None,
    ) -> PlayerMatchPerformance:
        match = next(
            (
                item
                for item in self.repository.list_matches(
                    club_id
                )
                if item.match_id == match_id
            ),
            None,
        )
        if match is None:
            raise KeyError("Maç bulunamadı")
        player = self.repository.get_player(
            club_id=club_id,
            player_id=player_id,
        )
        if player is None:
            raise KeyError("Oyuncu bulunamadı")
        if not 0 <= minutes <= 130:
            raise MVPValidationError(
                "Dakika 0 ile 130 arasında olmalıdır"
            )
        if goals < 0 or assists < 0:
            raise MVPValidationError(
                "Gol ve asist negatif olamaz"
            )
        if not 0 <= rating <= 10:
            raise MVPValidationError(
                "Puan 0 ile 10 arasında olmalıdır"
            )
        item = PlayerMatchPerformance(
            match_id=match_id,
            club_id=club_id,
            player_id=player_id,
            minutes=minutes,
            goals=goals,
            assists=assists,
            rating=rating,
            note=note.strip(),
            recorded_at=int(
                now if now is not None
                else time.time()
            ),
        )
        return self.repository.save_performance(
            item
        )

    def save_match_report(
        self,
        *,
        match_id: str,
        club_id: str,
        summary: str,
        positives: str,
        improvements: str,
        now: int | None = None,
    ) -> MatchReport:
        match = next(
            (
                item
                for item in self.repository.list_matches(
                    club_id
                )
                if item.match_id == match_id
            ),
            None,
        )
        if match is None:
            raise KeyError("Maç bulunamadı")
        if len(summary.strip()) < 5:
            raise MVPValidationError(
                "Maç özeti çok kısa"
            )
        item = MatchReport(
            match_id=match_id,
            club_id=club_id,
            summary=summary.strip(),
            positives=positives.strip(),
            improvements=improvements.strip(),
            created_at=int(
                now if now is not None
                else time.time()
            ),
        )
        return self.repository.save_match_report(
            item
        )

    def player_form(
        self,
        *,
        club_id: str,
    ) -> tuple[dict, ...]:
        players = self.repository.list_players(
            club_id
        )
        matches = self.repository.list_matches(
            club_id
        )
        rows = []
        for player in players:
            performances = [
                item
                for match in matches
                for item in (
                    self.repository.list_performances(
                        match.match_id
                    )
                )
                if item.player_id == player.player_id
            ]
            if performances:
                average = round(
                    sum(item.rating for item in performances)
                    / len(performances),
                    2,
                )
                minutes = sum(
                    item.minutes for item in performances
                )
                goals = sum(
                    item.goals for item in performances
                )
                assists = sum(
                    item.assists for item in performances
                )
            else:
                average = 0.0
                minutes = goals = assists = 0
            rows.append({
                "player_id": player.player_id,
                "name": player.name,
                "position": player.position,
                "matches": len(performances),
                "minutes": minutes,
                "goals": goals,
                "assists": assists,
                "average_rating": average,
            })
        rows.sort(
            key=lambda item: (
                item["average_rating"],
                item["goals"],
                item["assists"],
            ),
            reverse=True,
        )
        return tuple(rows)


    def save_opponent_profile(
        self,
        *,
        opponent_id: str,
        club_id: str,
        name: str,
        formation: str,
        strengths: tuple[str, ...],
        weaknesses: tuple[str, ...],
        key_players: tuple[str, ...],
        notes: str,
        now: int | None = None,
    ) -> OpponentProfile:
        if self.repository.get_club(club_id) is None:
            raise KeyError("Kulüp bulunamadı")
        if len(name.strip()) < 2:
            raise MVPValidationError(
                "Rakip adı çok kısa"
            )
        item = OpponentProfile(
            opponent_id=opponent_id,
            club_id=club_id,
            name=name.strip(),
            formation=formation.strip(),
            strengths=tuple(
                item.strip()
                for item in strengths
                if item.strip()
            ),
            weaknesses=tuple(
                item.strip()
                for item in weaknesses
                if item.strip()
            ),
            key_players=tuple(
                item.strip()
                for item in key_players
                if item.strip()
            ),
            notes=notes.strip(),
            updated_at=int(
                now if now is not None
                else time.time()
            ),
        )
        return self.repository.save_opponent(
            item
        )

    def create_match_preparation(
        self,
        *,
        preparation_id: str,
        match_id: str,
        club_id: str,
        opponent_id: str,
        tactical_plan: str,
        pressing_plan: str,
        set_piece_plan: str,
        objectives: tuple[str, ...],
        now: int | None = None,
    ) -> MatchPreparation:
        match = next(
            (
                item
                for item in self.repository.list_matches(
                    club_id
                )
                if item.match_id == match_id
            ),
            None,
        )
        if match is None:
            raise KeyError("Maç bulunamadı")
        opponent = self.repository.get_opponent(
            club_id=club_id,
            opponent_id=opponent_id,
        )
        if opponent is None:
            raise KeyError("Rakip profili bulunamadı")
        if len(tactical_plan.strip()) < 5:
            raise MVPValidationError(
                "Taktik plan çok kısa"
            )
        current = int(
            now if now is not None
            else time.time()
        )
        item = MatchPreparation(
            preparation_id=preparation_id,
            match_id=match_id,
            club_id=club_id,
            opponent_id=opponent_id,
            tactical_plan=tactical_plan.strip(),
            pressing_plan=pressing_plan.strip(),
            set_piece_plan=set_piece_plan.strip(),
            objectives=tuple(
                item.strip()
                for item in objectives
                if item.strip()
            ),
            status="DRAFT",
            created_at=current,
            updated_at=current,
        )
        return self.repository.save_preparation(
            item
        )

    def transition_preparation(
        self,
        *,
        preparation_id: str,
        target_status: str,
        now: int | None = None,
    ) -> MatchPreparation:
        item = self.repository.get_preparation(
            preparation_id
        )
        if item is None:
            raise KeyError(
                "Maç hazırlık planı bulunamadı"
            )
        transitions = {
            "DRAFT": {"READY", "CANCELLED"},
            "READY": {"COMPLETED", "DRAFT"},
            "COMPLETED": set(),
            "CANCELLED": set(),
        }
        target = target_status.upper()
        if target not in transitions[item.status]:
            raise MVPValidationError(
                f"Geçersiz hazırlık geçişi: "
                f"{item.status} -> {target}"
            )
        updated = MatchPreparation(
            **{
                **item.__dict__,
                "status": target,
                "updated_at": int(
                    now if now is not None
                    else time.time()
                ),
            }
        )
        return self.repository.save_preparation(
            updated
        )

    def seed_demo(
        self,
        *,
        now: int | None = None,
    ) -> dict:
        current = int(
            now if now is not None else time.time()
        )
        club_id = "demo-aslan"
        if self.repository.get_club(club_id) is None:
            self.create_club(
                club_id=club_id,
                name="Aslan Demo FK",
                country="Türkiye",
                now=current,
            )

        demo_players = (
            ("demo-p1", "Emir Kaya", "GK", 25, 2.4),
            ("demo-p2", "Mert Demir", "CB", 24, 3.8),
            ("demo-p3", "Arda Şahin", "CM", 22, 5.2),
            ("demo-p4", "Kerem Akın", "RW", 21, 6.1),
            ("demo-p5", "Can Yıldız", "ST", 26, 7.5),
        )
        for player_id, name, position, age, value in demo_players:
            if self.repository.get_player(
                club_id=club_id,
                player_id=player_id,
            ) is None:
                self.create_player(
                    player_id=player_id,
                    club_id=club_id,
                    name=name,
                    position=position,
                    age=age,
                    market_value=value,
                    now=current,
                )

        existing_matches = {
            item.match_id
            for item in self.repository.list_matches(
                club_id
            )
        }
        if "demo-m1" not in existing_matches:
            self.create_match(
                match_id="demo-m1",
                club_id=club_id,
                opponent="Mavişehir SK",
                competition="Hazırlık",
                kickoff_at=current - 86400,
                venue="HOME",
                now=current,
            )
            self.complete_match(
                match_id="demo-m1",
                club_id=club_id,
                goals_for=3,
                goals_against=1,
            )
        if "demo-m2" not in existing_matches:
            self.create_match(
                match_id="demo-m2",
                club_id=club_id,
                opponent="Kuzey FK",
                competition="Lig",
                kickoff_at=current + 86400,
                venue="AWAY",
                now=current,
            )
        return self.dashboard(club_id=club_id)

    def dashboard(self, *, club_id: str) -> dict:
        club = self.repository.get_club(club_id)
        if club is None:
            raise KeyError("Kulüp bulunamadı")
        players = self.repository.list_players(club_id)
        matches = self.repository.list_matches(club_id)
        completed = [m for m in matches if m.status == "COMPLETED"]
        wins = sum(
            1
            for m in completed
            if (m.goals_for or 0) > (m.goals_against or 0)
        )
        draws = sum(
            1
            for m in completed
            if m.goals_for == m.goals_against
        )
        losses = len(completed) - wins - draws
        squad_value = round(
            sum(item.market_value for item in players),
            2,
        )
        availability = {}
        for item in players:
            availability[item.availability] = (
                availability.get(item.availability, 0)
                + 1
            )
        trainings = self.repository.list_trainings(
            club_id
        )
        return {
            "club": club.__dict__,
            "summary": {
                "player_count": len(players),
                "available_players": availability.get(
                    "AVAILABLE",
                    0,
                ),
                "unavailable_players": sum(
                    value
                    for key, value in availability.items()
                    if key != "AVAILABLE"
                ),
                "squad_value": squad_value,
                "completed_matches": len(completed),
                "wins": wins,
                "draws": draws,
                "losses": losses,
            },
            "players": [item.__dict__ for item in players],
            "matches": [
                {
                    **item.__dict__,
                    "squad": (
                        list(squad.player_ids)
                        if (
                            squad := self.repository.get_squad(
                                item.match_id
                            )
                        )
                        else []
                    ),
                    "performances": [
                        row.__dict__
                        for row in (
                            self.repository.list_performances(
                                item.match_id
                            )
                        )
                    ],
                    "report": (
                        report.__dict__
                        if (
                            report := self.repository.get_match_report(
                                item.match_id
                            )
                        )
                        else None
                    ),
                    "preparations": [
                        {
                            **row.__dict__,
                            "objectives": list(
                                row.objectives
                            ),
                        }
                        for row in (
                            self.repository.list_preparations(
                                item.match_id
                            )
                        )
                    ],
                }
                for item in matches[:10]
            ],
            "trainings": [
                {
                    **item.__dict__,
                    "attendance": [
                        row.__dict__
                        for row in (
                            self.repository.list_attendance(
                                item.session_id
                            )
                        )
                    ],
                }
                for item in trainings[:10]
            ],
            "opponents": [
                {
                    **item.__dict__,
                    "strengths": list(item.strengths),
                    "weaknesses": list(item.weaknesses),
                    "key_players": list(item.key_players),
                }
                for item in (
                    self.repository.list_opponents(
                        club_id
                    )
                )
            ],
        }
