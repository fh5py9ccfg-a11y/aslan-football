from __future__ import annotations

from pathlib import Path
import secrets


SECRET_FIELDS = {
    "AUTH_TOKEN_SECRET": 48,
    "MVP_AUTH_SECRET": 48,
    "SESSION_MAINTENANCE_APPROVAL_SIGNING_SECRET": 48,
    "COMPLIANCE_ATTESTATION_SECRET": 48,
    "PROVIDER_API_KEY": 32,
}

INSECURE_MARKERS = (
    "change-this",
    "change-me",
    "local-pilot-secret",
)


def is_insecure(value: str) -> bool:
    lowered = value.lower()
    return (
        len(value) < 24
        or any(marker in lowered for marker in INSECURE_MARKERS)
    )


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    env_path = root / ".env"
    example_path = root / ".env.example"

    if not env_path.exists():
        env_path.write_text(
            example_path.read_text(encoding="utf-8"),
            encoding="utf-8",
        )

    output: list[str] = []
    seen: set[str] = set()

    for line in env_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in line:
            output.append(line)
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        seen.add(key)

        if key in SECRET_FIELDS and is_insecure(value):
            value = secrets.token_urlsafe(SECRET_FIELDS[key])
        elif key == "APP_ENV" and value.strip() == "development":
            value = "production"

        output.append(f"{key}={value}")

    for key, length in SECRET_FIELDS.items():
        if key not in seen:
            output.append(f"{key}={secrets.token_urlsafe(length)}")

    env_path.write_text("\n".join(output) + "\n", encoding="utf-8")
    print(f"Güvenli ortam dosyası hazır: {env_path}")


if __name__ == "__main__":
    main()
