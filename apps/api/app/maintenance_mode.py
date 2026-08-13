from __future__ import annotations


async def maintenance_mode_middleware(request, call_next):
    controller = request.app.state.maintenance_controller
    exempt = {
        "/health",
        "/ready",
        "/live",
        "/metrics",
    }

    if (
        controller.enabled
        and request.url.path not in exempt
        and not request.url.path.startswith(
            "/admin/production-readiness"
        )
    ):
        from fastapi.responses import JSONResponse

        return JSONResponse(
            status_code=503,
            content={
                "detail": "Platform bakım modunda",
                "reason": controller.reason,
                "retryable": True,
            },
            headers={"Retry-After": "30"},
        )

    return await call_next(request)
