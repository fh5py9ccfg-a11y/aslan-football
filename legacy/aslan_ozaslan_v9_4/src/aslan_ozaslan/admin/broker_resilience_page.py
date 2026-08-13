from __future__ import annotations
import html

def render_broker_resilience_page(
    *,
    health,
    retry_policy,
    dead_letter_count: int,
    schema_count: int,
) -> str:
    error = html.escape(health.error) if health.error else "Yok"
    return (
        "<!doctype html><html lang='tr'><head><meta charset='utf-8'>"
        "<title>Aslan Özaslan Broker Resilience</title></head><body>"
        "<h1>Broker Resilience Center</h1>"
        f"<p>Broker sağlıklı: {health.healthy}</p>"
        f"<p>Gecikme: {health.latency_ms:.2f} ms</p>"
        f"<p>Hata: {error}</p>"
        f"<p>Maksimum retry: {retry_policy.max_attempts}</p>"
        f"<p>Dead-letter sayısı: {dead_letter_count}</p>"
        f"<p>Kayıtlı şema: {schema_count}</p>"
        "</body></html>"
    )
