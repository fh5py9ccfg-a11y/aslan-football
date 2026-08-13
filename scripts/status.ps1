$ErrorActionPreference = "Stop"

docker compose ps --all
python scripts/diagnose.py
