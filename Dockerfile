FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY pyproject.toml alembic.ini /app/
COPY migrations /app/migrations
COPY packages /app/packages
COPY apps /app/apps
COPY QUICK_ENSEMBLE_MODEL.json /app/QUICK_ENSEMBLE_MODEL.json
COPY QUICK_BASELINE_MODEL.json /app/QUICK_BASELINE_MODEL.json
COPY scripts/cloud_start.sh /app/scripts/cloud_start.sh

RUN pip install --no-cache-dir -e . \
    && chmod +x /app/scripts/cloud_start.sh

ENV PYTHONPATH=/app/packages/football_core/src:/app

EXPOSE 10000

CMD ["/app/scripts/cloud_start.sh"]
