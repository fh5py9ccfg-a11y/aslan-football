from .settings import settings

def database_ready():
    if settings.environment == "test":
        return True, "test_repository"
    try:
        from sqlalchemy import text
        from .db import SessionLocal
        with SessionLocal.begin() as session:
            session.execute(text("SELECT 1"))
        return True, "ok"
    except Exception as exc:
        return False, str(exc)

def provider_ready():
    return (
        (True, "configured")
        if settings.sportmonks_api_token
        else (False, "token_missing")
    )
