from __future__ import annotations

import html


def render_certificate_events_page(events) -> str:
    rows = "".join(
        "<tr>"
        f"<td>{html.escape(event.occurred_at)}</td>"
        f"<td>{html.escape(event.certificate_name)}</td>"
        f"<td>{html.escape(event.event_type)}</td>"
        f"<td>{html.escape(event.detail)}</td>"
        "</tr>"
        for event in events
    )
    return (
        "<!doctype html><html lang='tr'><head><meta charset='utf-8'>"
        "<title>Aslan Özaslan Sertifika Olayları</title></head><body>"
        "<h1>Sertifika Olay Geçmişi</h1>"
        "<table><thead><tr>"
        "<th>Zaman</th><th>Sertifika</th><th>Olay</th><th>Detay</th>"
        "</tr></thead><tbody>"
        f"{rows}</tbody></table>"
        "</body></html>"
    )
