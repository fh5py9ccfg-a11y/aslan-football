import os
from starlette.responses import JSONResponse

MAX_REQUEST_BYTES = int(
    os.getenv("MAX_REQUEST_BYTES", "1048576")
)

async def request_size_middleware(
    request,
    call_next,
):
    content_length = request.headers.get(
        "Content-Length"
    )
    if content_length is not None:
        try:
            size = int(content_length)
        except ValueError:
            return JSONResponse(
                status_code=400,
                content={
                    "detail": "Content-Length geçersiz"
                },
            )
        if size > MAX_REQUEST_BYTES:
            return JSONResponse(
                status_code=413,
                content={
                    "detail": "İstek gövdesi çok büyük"
                },
            )
    return await call_next(request)
