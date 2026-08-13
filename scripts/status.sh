#!/usr/bin/env sh
set -eu

docker compose ps --all
python scripts/diagnose.py
