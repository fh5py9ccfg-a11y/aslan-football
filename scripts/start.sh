#!/usr/bin/env sh
set -eu

python scripts/bootstrap_env.py
docker compose up --build -d
python scripts/wait_for_ready.py
python scripts/final_pilot_setup.py
python scripts/pilot_acceptance.py
python scripts/diagnose.py

echo ""
echo "Aslan Football hazır: http://localhost:8000"
