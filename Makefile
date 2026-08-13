.PHONY: test api up down integration live

test:
	pytest -q

api:
	PYTHONPATH=packages/football_core/src:. APP_ENV=test uvicorn apps.api.app.main:app --reload

up:
	docker compose up --build

down:
	docker compose down

integration:
	RUN_CONTAINER_INTEGRATION=1 docker compose -f docker-compose.yml -f docker-compose.integration.yml run --rm integration-tests

live:
	docker compose --profile live up --build
