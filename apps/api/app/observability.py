import json, logging, time, uuid
from contextvars import ContextVar

correlation_id_var = ContextVar("correlation_id", default="")

class JsonFormatter(logging.Formatter):
    def format(self, record):
        return json.dumps({
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "correlation_id": correlation_id_var.get(),
        }, ensure_ascii=False)

def configure_logging():
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(logging.INFO)

async def correlation_middleware(request, call_next):
    correlation_id = (
        request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
    )
    token = correlation_id_var.set(correlation_id)
    started = time.perf_counter()
    try:
        response = await call_next(request)
        response.headers["X-Correlation-ID"] = correlation_id
        response.headers["X-Process-Time-Ms"] = (
            f"{(time.perf_counter() - started) * 1000:.2f}"
        )
        return response
    finally:
        correlation_id_var.reset(token)
