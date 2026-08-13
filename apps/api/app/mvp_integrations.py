from __future__ import annotations

from dataclasses import dataclass
import csv
import io
import json
import time


@dataclass(frozen=True)
class ProviderConnection:
    connection_id: str
    club_id: str
    provider: str
    base_url: str
    external_club_id: str
    status: str
    created_at: int
    updated_at: int


@dataclass(frozen=True)
class SyncRun:
    sync_id: str
    connection_id: str
    club_id: str
    entity_type: str
    status: str
    imported: int
    skipped: int
    failed: int
    errors: tuple[str, ...]
    started_at: int
    completed_at: int


class IntegrationValidationError(ValueError):
    pass


class RedisMVPIntegrationRepository:
    def __init__(
        self,
        client,
        *,
        prefix: str = "aslan:mvp-integrations",
        ttl_seconds: int = 31_536_000,
    ):
        self.client = client
        self.prefix = prefix
        self.ttl_seconds = ttl_seconds

    def save_connection(
        self,
        item: ProviderConnection,
    ) -> ProviderConnection:
        self.client.setex(
            self._connection_key(item.connection_id),
            self.ttl_seconds,
            json.dumps(
                item.__dict__,
                ensure_ascii=False,
            ),
        )
        self.client.sadd(
            self._club_connection_index(item.club_id),
            item.connection_id,
        )
        return item

    def get_connection(
        self,
        connection_id: str,
    ) -> ProviderConnection | None:
        payload = self.client.get(
            self._connection_key(connection_id)
        )
        if payload is None:
            return None
        if isinstance(payload, bytes):
            payload = payload.decode("utf-8")
        return ProviderConnection(**json.loads(payload))

    def list_connections(
        self,
        club_id: str,
    ) -> tuple[ProviderConnection, ...]:
        items = []
        for connection_id in self.client.smembers(
            self._club_connection_index(club_id)
        ):
            if isinstance(connection_id, bytes):
                connection_id = connection_id.decode("utf-8")
            item = self.get_connection(str(connection_id))
            if item is not None:
                items.append(item)
        items.sort(key=lambda item: item.created_at)
        return tuple(items)

    def save_sync(
        self,
        item: SyncRun,
    ) -> SyncRun:
        payload = {
            **item.__dict__,
            "errors": list(item.errors),
        }
        self.client.setex(
            self._sync_key(item.sync_id),
            self.ttl_seconds,
            json.dumps(
                payload,
                ensure_ascii=False,
            ),
        )
        self.client.sadd(
            self._club_sync_index(item.club_id),
            item.sync_id,
        )
        return item

    def list_syncs(
        self,
        club_id: str,
    ) -> tuple[SyncRun, ...]:
        items = []
        for sync_id in self.client.smembers(
            self._club_sync_index(club_id)
        ):
            if isinstance(sync_id, bytes):
                sync_id = sync_id.decode("utf-8")
            payload = self.client.get(
                self._sync_key(str(sync_id))
            )
            if payload is None:
                continue
            if isinstance(payload, bytes):
                payload = payload.decode("utf-8")
            data = json.loads(payload)
            data["errors"] = tuple(data["errors"])
            items.append(SyncRun(**data))
        items.sort(
            key=lambda item: item.started_at,
            reverse=True,
        )
        return tuple(items)

    def _connection_key(self, connection_id: str) -> str:
        return f"{self.prefix}:connection:{connection_id}"

    def _club_connection_index(self, club_id: str) -> str:
        return f"{self.prefix}:connections:{club_id}"

    def _sync_key(self, sync_id: str) -> str:
        return f"{self.prefix}:sync:{sync_id}"

    def _club_sync_index(self, club_id: str) -> str:
        return f"{self.prefix}:syncs:{club_id}"


class MVPIntegrationService:
    SUPPORTED_PROVIDERS = {
        "CSV",
        "GENERIC_JSON",
        "MANUAL_API",
    }

    def __init__(
        self,
        *,
        repository,
        workspace_service,
    ):
        self.repository = repository
        self.workspace_service = workspace_service

    def create_connection(
        self,
        *,
        connection_id: str,
        club_id: str,
        provider: str,
        base_url: str,
        external_club_id: str,
        now: int | None = None,
    ) -> ProviderConnection:
        if self.workspace_service.repository.get_club(club_id) is None:
            raise KeyError("Kulüp bulunamadı")
        normalized = provider.upper()
        if normalized not in self.SUPPORTED_PROVIDERS:
            raise IntegrationValidationError(
                "Desteklenmeyen provider"
            )
        current = int(now if now is not None else time.time())
        item = ProviderConnection(
            connection_id=connection_id,
            club_id=club_id,
            provider=normalized,
            base_url=base_url.strip(),
            external_club_id=external_club_id.strip(),
            status="ACTIVE",
            created_at=current,
            updated_at=current,
        )
        return self.repository.save_connection(item)

    def import_players_csv(
        self,
        *,
        sync_id: str,
        club_id: str,
        csv_text: str,
        now: int | None = None,
    ) -> SyncRun:
        current = int(now if now is not None else time.time())
        imported = skipped = failed = 0
        errors: list[str] = []

        reader = csv.DictReader(io.StringIO(csv_text))
        required = {
            "player_id",
            "name",
            "position",
            "age",
            "market_value",
        }
        if not reader.fieldnames or not required.issubset(
            set(reader.fieldnames)
        ):
            raise IntegrationValidationError(
                "Oyuncu CSV kolonları eksik"
            )

        existing = {
            item.player_id
            for item in self.workspace_service
            .repository.list_players(club_id)
        }

        for row_number, row in enumerate(reader, start=2):
            try:
                player_id = (row["player_id"] or "").strip()
                if not player_id:
                    raise ValueError("player_id boş")
                if player_id in existing:
                    skipped += 1
                    continue
                self.workspace_service.create_player(
                    player_id=player_id,
                    club_id=club_id,
                    name=(row["name"] or "").strip(),
                    position=(row["position"] or "").strip(),
                    age=int(row["age"]),
                    market_value=float(row["market_value"]),
                    now=current,
                )
                existing.add(player_id)
                imported += 1
            except Exception as exc:
                failed += 1
                errors.append(
                    f"Satır {row_number}: {exc}"
                )

        status = (
            "COMPLETED"
            if failed == 0
            else "PARTIAL"
            if imported > 0
            else "FAILED"
        )
        item = SyncRun(
            sync_id=sync_id,
            connection_id="csv-upload",
            club_id=club_id,
            entity_type="PLAYERS",
            status=status,
            imported=imported,
            skipped=skipped,
            failed=failed,
            errors=tuple(errors),
            started_at=current,
            completed_at=current,
        )
        return self.repository.save_sync(item)

    def import_fixtures_csv(
        self,
        *,
        sync_id: str,
        club_id: str,
        csv_text: str,
        now: int | None = None,
    ) -> SyncRun:
        current = int(now if now is not None else time.time())
        imported = skipped = failed = 0
        errors: list[str] = []

        reader = csv.DictReader(io.StringIO(csv_text))
        required = {
            "match_id",
            "opponent",
            "competition",
            "kickoff_at",
            "venue",
        }
        if not reader.fieldnames or not required.issubset(
            set(reader.fieldnames)
        ):
            raise IntegrationValidationError(
                "Fikstür CSV kolonları eksik"
            )

        existing = {
            item.match_id
            for item in self.workspace_service
            .repository.list_matches(club_id)
        }

        for row_number, row in enumerate(reader, start=2):
            try:
                match_id = (row["match_id"] or "").strip()
                if not match_id:
                    raise ValueError("match_id boş")
                if match_id in existing:
                    skipped += 1
                    continue
                self.workspace_service.create_match(
                    match_id=match_id,
                    club_id=club_id,
                    opponent=(row["opponent"] or "").strip(),
                    competition=(row["competition"] or "").strip(),
                    kickoff_at=int(row["kickoff_at"]),
                    venue=(row["venue"] or "").strip().upper(),
                    now=current,
                )
                existing.add(match_id)
                imported += 1
            except Exception as exc:
                failed += 1
                errors.append(
                    f"Satır {row_number}: {exc}"
                )

        status = (
            "COMPLETED"
            if failed == 0
            else "PARTIAL"
            if imported > 0
            else "FAILED"
        )
        item = SyncRun(
            sync_id=sync_id,
            connection_id="csv-upload",
            club_id=club_id,
            entity_type="FIXTURES",
            status=status,
            imported=imported,
            skipped=skipped,
            failed=failed,
            errors=tuple(errors),
            started_at=current,
            completed_at=current,
        )
        return self.repository.save_sync(item)

    def provider_payload_preview(
        self,
        *,
        connection_id: str,
        payload_json: str,
    ) -> dict:
        connection = self.repository.get_connection(
            connection_id
        )
        if connection is None:
            raise KeyError("Provider bağlantısı bulunamadı")
        try:
            payload = json.loads(payload_json)
        except json.JSONDecodeError as exc:
            raise IntegrationValidationError(
                "Geçersiz provider JSON"
            ) from exc
        if not isinstance(payload, dict):
            raise IntegrationValidationError(
                "Provider payload JSON object olmalıdır"
            )
        return {
            "connection_id": connection_id,
            "provider": connection.provider,
            "external_club_id": connection.external_club_id,
            "top_level_fields": sorted(payload.keys()),
            "record_count": (
                len(payload.get("items", []))
                if isinstance(payload.get("items"), list)
                else 1
            ),
        }
