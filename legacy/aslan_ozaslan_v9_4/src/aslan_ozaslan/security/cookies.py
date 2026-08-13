from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CookiePolicy:
    name: str = "aslan_session"
    secure: bool = True
    http_only: bool = True
    same_site: str = "Strict"
    path: str = "/"
    max_age_seconds: int = 3600

    def header(self, value: str) -> str:
        if not value:
            raise ValueError("Cookie değeri boş olamaz")
        parts = [f"{self.name}={value}", f"Path={self.path}", f"Max-Age={self.max_age_seconds}"]
        if self.http_only:
            parts.append("HttpOnly")
        if self.secure:
            parts.append("Secure")
        parts.append(f"SameSite={self.same_site}")
        return "; ".join(parts)

    def clear_header(self) -> str:
        return (
            f"{self.name}=; Path={self.path}; Max-Age=0; "
            f"HttpOnly; Secure; SameSite={self.same_site}"
        )
