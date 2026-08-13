from __future__ import annotations
from dataclasses import dataclass
from typing import Callable

@dataclass(frozen=True)
class SchemaDefinition:
    name: str
    version: int
    validator: Callable[[dict], None]

class SchemaRegistry:
    def __init__(self):
        self._schemas: dict[tuple[str, int], SchemaDefinition] = {}

    def register(self, schema: SchemaDefinition) -> None:
        if not schema.name.strip():
            raise ValueError("Şema adı boş olamaz")
        if schema.version <= 0:
            raise ValueError("Şema sürümü pozitif olmalıdır")
        self._schemas[(schema.name, schema.version)] = schema

    def validate(self, name: str, version: int, payload: dict) -> None:
        schema = self._schemas.get((name, version))
        if schema is None:
            raise KeyError(f"Şema bulunamadı: {name} v{version}")
        schema.validator(payload)

def require_fields(*fields: str):
    required = tuple(fields)
    def validator(payload: dict) -> None:
        if not isinstance(payload, dict):
            raise ValueError("Payload nesne olmalıdır")
        missing = [field for field in required if field not in payload]
        if missing:
            raise ValueError("Eksik alanlar: " + ", ".join(missing))
    return validator
