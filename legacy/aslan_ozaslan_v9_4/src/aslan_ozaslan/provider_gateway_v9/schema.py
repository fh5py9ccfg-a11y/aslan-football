from __future__ import annotations

from .domain import PayloadValidationResult

class SportmonksPayloadSchemaValidator:
    SUPPORTED_EVENT_TYPES = {
        "goal",
        "yellowcard",
        "redcard",
        "substitution",
        "var",
        "penalty",
        "missed_penalty",
    }

    def validate_fixture(self, payload: dict) -> PayloadValidationResult:
        errors = []
        warnings = []

        if not isinstance(payload, dict):
            return PayloadValidationResult(False, ("payload_not_object",), ())

        if payload.get("id") in (None, ""):
            errors.append("fixture_id_missing")

        participants = payload.get("participants") or []
        if len(participants) < 2:
            errors.append("fixture_participants_missing")
        else:
            locations = {
                str(item.get("meta", {}).get("location", "")).lower()
                for item in participants
            }
            if "home" not in locations or "away" not in locations:
                warnings.append("participant_locations_incomplete")

        state = payload.get("state") or {}
        if not state:
            warnings.append("fixture_state_missing")

        minute = state.get("minute")
        if minute is not None:
            try:
                parsed = int(minute)
                if parsed < 0 or parsed > 130:
                    errors.append("fixture_minute_invalid")
            except (TypeError, ValueError):
                errors.append("fixture_minute_invalid")

        return PayloadValidationResult(
            valid=not errors,
            errors=tuple(sorted(set(errors))),
            warnings=tuple(sorted(set(warnings))),
        )

    def validate_player(self, payload: dict) -> PayloadValidationResult:
        errors = []
        warnings = []

        if not isinstance(payload, dict):
            return PayloadValidationResult(False, ("payload_not_object",), ())

        if payload.get("id") in (None, ""):
            errors.append("player_id_missing")
        if not (payload.get("display_name") or payload.get("name")):
            errors.append("player_name_missing")
        if payload.get("position_id") is None:
            warnings.append("player_position_missing")
        if payload.get("date_of_birth") is None:
            warnings.append("player_date_of_birth_missing")

        return PayloadValidationResult(
            valid=not errors,
            errors=tuple(sorted(set(errors))),
            warnings=tuple(sorted(set(warnings))),
        )

    def validate_event(self, payload: dict) -> PayloadValidationResult:
        errors = []
        warnings = []

        if not isinstance(payload, dict):
            return PayloadValidationResult(False, ("payload_not_object",), ())

        if payload.get("id") in (None, ""):
            errors.append("event_id_missing")
        if payload.get("fixture_id") in (None, ""):
            errors.append("event_fixture_id_missing")

        minute = payload.get("minute")
        try:
            parsed_minute = int(minute)
            if parsed_minute < 0 or parsed_minute > 130:
                errors.append("event_minute_invalid")
        except (TypeError, ValueError):
            errors.append("event_minute_invalid")

        event_type = str(
            payload.get("type", {}).get("developer_name")
            or payload.get("type_name")
            or payload.get("type")
            or ""
        ).lower()

        if not event_type:
            errors.append("event_type_missing")
        elif event_type not in self.SUPPORTED_EVENT_TYPES:
            warnings.append("event_type_unmapped")

        return PayloadValidationResult(
            valid=not errors,
            errors=tuple(sorted(set(errors))),
            warnings=tuple(sorted(set(warnings))),
        )
