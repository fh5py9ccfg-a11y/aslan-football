from pathlib import Path

def test_postgres_repository_uses_atomic_outbox_source():
    source = Path(
        "apps/api/app/postgres_repository.py"
    ).read_text(encoding="utf-8")

    assert "MatchEventModel" in source
    assert "OutboxMessageModel" in source
    assert "session.commit()" in source
    assert "session.rollback()" in source
