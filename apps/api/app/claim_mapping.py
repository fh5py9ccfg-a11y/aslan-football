from __future__ import annotations
from dataclasses import dataclass
import json

@dataclass(frozen=True)
class ClaimMapping:
    roles_claims: tuple[str, ...]
    role_prefix: str
    subject_claim: str

    @classmethod
    def from_json(cls, raw: str | None) -> "ClaimMapping":
        if not raw:
            return cls(
                roles_claims=(
                    "roles",
                    "realm_access.roles",
                    "scope",
                ),
                role_prefix="role:",
                subject_claim="sub",
            )

        payload = json.loads(raw)
        claims = payload.get("roles_claims") or ()
        if not isinstance(claims, list):
            raise ValueError("roles_claims liste olmalıdır")

        return cls(
            roles_claims=tuple(str(item) for item in claims),
            role_prefix=str(payload.get("role_prefix", "role:")),
            subject_claim=str(payload.get("subject_claim", "sub")),
        )

class ClaimMapper:
    def __init__(self, mapping: ClaimMapping):
        self.mapping = mapping

    def subject(self, payload: dict) -> str:
        value = self._read_path(
            payload,
            self.mapping.subject_claim,
        )
        return str(value or "")

    def roles(self, payload: dict) -> tuple[str, ...]:
        values = []

        for path in self.mapping.roles_claims:
            value = self._read_path(payload, path)

            if isinstance(value, list):
                values.extend(str(item) for item in value)
                continue

            if isinstance(value, str):
                if path == "scope":
                    values.extend(
                        item.removeprefix(
                            self.mapping.role_prefix
                        )
                        for item in value.split()
                        if item.startswith(
                            self.mapping.role_prefix
                        )
                    )
                else:
                    values.append(value)

        result = []
        seen = set()
        for item in values:
            if item not in seen:
                seen.add(item)
                result.append(item)
        return tuple(result)

    @staticmethod
    def _read_path(payload: dict, path: str):
        value = payload
        for part in path.split("."):
            if not isinstance(value, dict):
                return None
            value = value.get(part)
        return value
