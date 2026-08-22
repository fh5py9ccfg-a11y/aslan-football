from app.comeback_routes import router as comeback_router


def _router_paths() -> list[str]:
    # FastAPI 0.141 stores the APIRouter prefix in each route path already.
    return [
        path
        for route in comeback_router.routes
        if (path := getattr(route, "path", None)) is not None
    ]


def test_comeback_routes_are_present():
    paths = set(_router_paths())

    assert "/api/comeback/health" in paths
    assert "/api/comeback/stored-readiness" in paths
    assert "/api/comeback/stored-candidates" in paths
    assert "/api/comeback/backtest" in paths
    assert "/api/comeback/self-check" in paths
    assert "/api/comeback/self-check.txt" in paths


def test_comeback_routes_have_unique_paths():
    comeback_paths = [
        path
        for path in _router_paths()
        if path.startswith("/api/comeback")
    ]

    assert len(comeback_paths) == len(set(comeback_paths))
