from fastapi import FastAPI

from app.comeback_routes import router as comeback_router


def test_comeback_routes_are_mountable_and_present():
    app = FastAPI()
    app.include_router(comeback_router)

    paths = {route.path for route in app.routes}

    assert "/api/comeback/health" in paths
    assert "/api/comeback/stored-readiness" in paths
    assert "/api/comeback/stored-candidates" in paths
    assert "/api/comeback/backtest" in paths
    assert "/api/comeback/self-check" in paths
    assert "/api/comeback/self-check.txt" in paths


def test_comeback_routes_have_unique_paths():
    app = FastAPI()
    app.include_router(comeback_router)

    comeback_paths = [
        route.path
        for route in app.routes
        if route.path.startswith("/api/comeback")
    ]

    assert len(comeback_paths) == len(set(comeback_paths))
