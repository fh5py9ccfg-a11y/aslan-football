from __future__ import annotations
import html

def render_decision_engine_page(report) -> str:
    snapshot = report.snapshot
    signals = "".join(
        "<tr>"
        f"<td>{html.escape(signal.signal_type)}</td>"
        f"<td>{html.escape(signal.side)}</td>"
        f"<td>{signal.strength:.3f}</td>"
        f"<td>{html.escape(signal.urgency)}</td>"
        f"<td>{html.escape(signal.explanation)}</td>"
        "</tr>"
        for signal in snapshot.signals
    ) or "<tr><td colspan='5'>Sinyal yok</td></tr>"

    return (
        "<!doctype html><html lang='tr'><head><meta charset='utf-8'>"
        "<title>Aslan Özaslan Real-Time Decision</title></head><body>"
        "<h1>Real-Time Decision Engine</h1>"
        f"<p>Fixture: {html.escape(snapshot.fixture_id)}</p>"
        f"<p>Dakika: {snapshot.minute}</p>"
        f"<p>Önerilen sonuç: {html.escape(snapshot.recommended_outcome)}</p>"
        f"<p>Güven: {snapshot.confidence:.3f}</p>"
        f"<p>Risk: {snapshot.risk_score:.3f}</p>"
        f"<p>Fırsat: {snapshot.opportunity_score:.3f}</p>"
        f"<p>Karar gecikmesi: {report.latency_ms:.3f} ms</p>"
        f"<p>Degraded: {report.degraded}</p>"
        "<h2>Sinyaller</h2>"
        "<table><thead><tr><th>Tür</th><th>Taraf</th><th>Güç</th>"
        "<th>Aciliyet</th><th>Açıklama</th></tr></thead>"
        f"<tbody>{signals}</tbody></table>"
        "</body></html>"
    )
