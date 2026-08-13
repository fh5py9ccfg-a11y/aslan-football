from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class GatewayResult:
    accepted: bool
    payload_type: str
    normalized: object | None
    errors: tuple[str, ...]
    warnings: tuple[str, ...]

class SportmonksPayloadGateway:
    def __init__(
        self,
        *,
        validator,
        normalizer,
        quarantine_repository,
    ):
        self.validator = validator
        self.normalizer = normalizer
        self.quarantine = quarantine_repository

    def process_fixture(self, payload: dict) -> GatewayResult:
        return self._process(
            payload_type="fixture",
            payload=payload,
            validate=self.validator.validate_fixture,
            normalize=self.normalizer.fixture,
        )

    def process_player(self, payload: dict) -> GatewayResult:
        return self._process(
            payload_type="player",
            payload=payload,
            validate=self.validator.validate_player,
            normalize=self.normalizer.player,
        )

    def process_event(self, payload: dict) -> GatewayResult:
        return self._process(
            payload_type="event",
            payload=payload,
            validate=self.validator.validate_event,
            normalize=self.normalizer.event,
        )

    def _process(
        self,
        *,
        payload_type,
        payload,
        validate,
        normalize,
    ) -> GatewayResult:
        validation = validate(payload)
        if not validation.valid:
            self.quarantine.add(
                payload_type=payload_type,
                payload=payload if isinstance(payload, dict) else {"raw": payload},
                errors=validation.errors,
                warnings=validation.warnings,
            )
            return GatewayResult(
                accepted=False,
                payload_type=payload_type,
                normalized=None,
                errors=validation.errors,
                warnings=validation.warnings,
            )

        try:
            normalized = normalize(payload)
        except Exception as exc:
            errors = ("normalization_failed",)
            self.quarantine.add(
                payload_type=payload_type,
                payload=payload,
                errors=errors,
                warnings=(str(exc),),
            )
            return GatewayResult(
                accepted=False,
                payload_type=payload_type,
                normalized=None,
                errors=errors,
                warnings=(str(exc),),
            )

        return GatewayResult(
            accepted=True,
            payload_type=payload_type,
            normalized=normalized,
            errors=(),
            warnings=validation.warnings,
        )
