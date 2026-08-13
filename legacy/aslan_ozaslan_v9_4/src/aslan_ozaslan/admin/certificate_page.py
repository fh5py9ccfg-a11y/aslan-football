from __future__ import annotations

import html


def render_certificate_page(alerts) -> str:
    rows = "".join(
        "<tr>"
        f"<td>{html.escape(alert.message)}</td>"
        f"<td>{alert.days_remaining}</td>"
        f"<td>{html.escape(alert.severity)}</td>"
        "</tr>"
        for alert in alerts
    )
    return (
        "<!doctype html><html lang='tr'><head><meta charset='utf-8'>"
        "<title>Aslan Özaslan Sertifikalar</title></head><body>"
        "<h1>Sertifika İzleme</h1>"
        "<table><thead><tr><th>Mesaj</th><th>Kalan gün</th><th>Seviye</th>"
        "</tr></thead><tbody>"
        f"{rows}</tbody></table>"
        "</body></html>"
    )
