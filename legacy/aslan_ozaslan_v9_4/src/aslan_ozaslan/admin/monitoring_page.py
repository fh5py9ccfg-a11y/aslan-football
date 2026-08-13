from __future__ import annotations
import html

def render_monitoring_page(snapshot, drift, safe_mode) -> str:
    reasons = "".join(
        f"<li>{html.escape(item)}</li>"
        for item in drift.reasons
    ) or "<li>Yok</li>"

    actions = "".join(
        f"<li>{html.escape(item)}</li>"
        for item in safe_mode.allowed_actions
    )

    return (
        "<!doctype html><html lang='tr'><head><meta charset='utf-8'>"
        "<title>Aslan Özaslan Decision Monitoring</title></head><body>"
        "<h1>Real-Time Decision Monitoring</h1>"
        f"<p>Örnek: {snapshot.samples}</p>"
        f"<p>Ortalama güven: {snapshot.average_confidence:.3f}</p>"
        f"<p>Ortalama risk: {snapshot.average_risk:.3f}</p>"
        f"<p>P95 gecikme: {snapshot.p95_latency_ms:.2f} ms</p>"
        f"<p>Degraded oranı: {snapshot.degraded_ratio:.3f}</p>"
        f"<p>Drift: {snapshot.drift_detected}</p>"
        f"<p>Circuit açık: {snapshot.circuit_open}</p>"
        f"<p>Safe mode: {snapshot.safe_mode}</p>"
        f"<h2>Drift nedenleri</h2><ul>{reasons}</ul>"
        f"<h2>İzin verilen işlemler</h2><ul>{actions}</ul>"
        "</body></html>"
    )
