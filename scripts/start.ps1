$ErrorActionPreference = "Stop"

python scripts/bootstrap_env.py
docker compose up --build -d
python scripts/wait_for_ready.py
python scripts/final_pilot_setup.py
python scripts/pilot_acceptance.py
python scripts/diagnose.py

Write-Host ""
Write-Host "Aslan Football hazır: http://localhost:8000"
