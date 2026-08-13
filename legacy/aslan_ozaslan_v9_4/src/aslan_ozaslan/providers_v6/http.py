from __future__ import annotations
from dataclasses import dataclass
from typing import Protocol

@dataclass(frozen=True)
class HttpResponse:
    status_code: int
    payload: dict

class HttpTransport(Protocol):
    def get(
        self,
        *,
        url: str,
        headers: dict[str, str],
        params: dict[str, str | int],
        timeout_seconds: float,
    ) -> HttpResponse: ...
