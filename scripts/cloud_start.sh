#!/usr/bin/env sh
set -eu

if [ -n "${DATABASE_URL:-}" ]; then
  case "$DATABASE_URL" in
    postgresql://*)
      export DATABASE_URL="postgresql+psycopg://${DATABASE_URL#postgresql://}"
      ;;
    postgres://*)
      export DATABASE_URL="postgresql+psycopg://${DATABASE_URL#postgres://}"
      ;;
  esac
fi

echo "Veritabanı geçişleri çalıştırılıyor..."
alembic upgrade head

PORT_VALUE="${PORT:-10000}"
echo "Sportmonks senkronizasyonu başlatılıyor..."
PYTHONPATH=/app/apps/worker python -m worker_app.sync_main &
echo "Sportmonks senkronizasyonu arka planda başlatıldı."

echo "Aslan Football başlatılıyor: port ${PORT_VALUE}"
exec uvicorn apps.api.app.main:app \
  --host 0.0.0.0 \
  --port "${PORT_VALUE}" \
  --proxy-headers \
  --forwarded-allow-ips="*"
