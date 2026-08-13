from __future__ import annotations
from .settings import settings
from .repository import InMemoryEventRepository

def build_event_repository():
    if settings.environment == "test":
        return InMemoryEventRepository()

    try:
        from .postgres_repository import PostgresEventRepository
        return PostgresEventRepository()
    except Exception:
        if settings.environment == "development":
            return InMemoryEventRepository()
        raise
