from __future__ import annotations
from pydantic import BaseModel
import os

class Settings(BaseModel):
    app_name: str = "Aslan Özaslan API"
    environment: str = os.getenv("APP_ENV", "development")
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://aslan:aslan@postgres:5432/aslan",
    )
    redis_url: str = os.getenv("REDIS_URL", "redis://redis:6379/0")
    sportmonks_api_token: str | None = os.getenv("SPORTMONKS_API_TOKEN")

settings = Settings()
