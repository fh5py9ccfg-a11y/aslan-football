from __future__ import annotations

from .domain import IngestionItemResult, BatchIngestionReport

class ProviderIngestionOrchestrator:
    def __init__(
        self,
        *,
        gateway,
        ledger,
        archive,
        fingerprint,
        event_projector=None,
    ):
        self.gateway = gateway
        self.ledger = ledger
        self.archive = archive
        self.fingerprint = fingerprint
        self.event_projector = event_projector

    def ingest(
        self,
        *,
        payload_type: str,
        payload: dict,
        provider: str = "sportmonks",
    ) -> IngestionItemResult:
        external_id = self._external_id(payload)
        payload_hash = self.fingerprint.calculate(payload)

        if self.ledger.is_completed(
            provider=provider,
            payload_type=payload_type,
            external_id=external_id,
            payload_hash=payload_hash,
        ):
            return IngestionItemResult(
                payload_type=payload_type,
                external_id=external_id,
                accepted=True,
                duplicate=True,
                archived=False,
                projected=False,
                quarantined=False,
                reason="already_completed",
            )

        self.ledger.mark(
            provider=provider,
            payload_type=payload_type,
            external_id=external_id,
            payload_hash=payload_hash,
            status="PROCESSING",
        )

        gateway_method = {
            "fixture": self.gateway.process_fixture,
            "player": self.gateway.process_player,
            "event": self.gateway.process_event,
        }.get(payload_type)

        if gateway_method is None:
            self.ledger.mark(
                provider=provider,
                payload_type=payload_type,
                external_id=external_id,
                payload_hash=payload_hash,
                status="FAILED",
                last_error="unsupported_payload_type",
            )
            return IngestionItemResult(
                payload_type=payload_type,
                external_id=external_id,
                accepted=False,
                duplicate=False,
                archived=False,
                projected=False,
                quarantined=False,
                reason="unsupported_payload_type",
            )

        gateway_result = gateway_method(payload)
        if not gateway_result.accepted:
            self.ledger.mark(
                provider=provider,
                payload_type=payload_type,
                external_id=external_id,
                payload_hash=payload_hash,
                status="QUARANTINED",
                last_error=",".join(gateway_result.errors),
            )
            return IngestionItemResult(
                payload_type=payload_type,
                external_id=external_id,
                accepted=False,
                duplicate=False,
                archived=False,
                projected=False,
                quarantined=True,
                reason="validation_failed",
            )

        archived = self.archive.append(
            provider=provider,
            payload_type=payload_type,
            external_id=external_id,
            payload_hash=payload_hash,
            payload=payload,
        )

        projected = False
        if (
            payload_type == "event"
            and self.event_projector is not None
        ):
            projected = self.event_projector.project(
                gateway_result.normalized
            )

        self.ledger.mark(
            provider=provider,
            payload_type=payload_type,
            external_id=external_id,
            payload_hash=payload_hash,
            status="COMPLETED",
        )

        return IngestionItemResult(
            payload_type=payload_type,
            external_id=external_id,
            accepted=True,
            duplicate=not archived,
            archived=archived,
            projected=projected,
            quarantined=False,
            reason="completed",
        )

    def ingest_batch(
        self,
        *,
        payload_type: str,
        payloads: list[dict],
        provider: str = "sportmonks",
    ) -> BatchIngestionReport:
        results = tuple(
            self.ingest(
                payload_type=payload_type,
                payload=payload,
                provider=provider,
            )
            for payload in payloads
        )
        return BatchIngestionReport(
            total=len(results),
            accepted=sum(1 for item in results if item.accepted),
            duplicates=sum(1 for item in results if item.duplicate),
            quarantined=sum(1 for item in results if item.quarantined),
            failed=sum(
                1 for item in results
                if not item.accepted and not item.quarantined
            ),
            results=results,
        )

    def _external_id(self, payload: dict) -> str:
        value = payload.get("id")
        return str(value) if value not in (None, "") else "unknown"
