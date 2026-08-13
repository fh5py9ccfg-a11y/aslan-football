#!/usr/bin/env sh
set -eu

docker compose up --build -d
python scripts/final_pilot_setup.py
