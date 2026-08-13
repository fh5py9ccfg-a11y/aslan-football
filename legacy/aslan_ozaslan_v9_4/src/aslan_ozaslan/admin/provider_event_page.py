from __future__ import annotations
import html

def render_provider_event_page(update, record) -> str:
    issues = "".join(
        f"<li>{html.escape(item)}</li>"
        for item in update.issues
    ) or "<li>Yok</li>"

    return (
        "<!doctype html><html lang='tr'><head><meta charset='utf-8'>"
        "<title>Aslan Özaslan Provider Events</title></head><body>"
        "<h1>Provider Event Reconciliation</h1>"
        f"<p>Event: {html.escape(record.provider_event_id)}</p>"
        f"<p>Tür: {html.escape(record.event_type)}</p>"
        f"<p>Dakika: {record.minute}</p>"
        f"<p>Değişti: {update.changed}</p>"
        f"<p>Replay gerekli: {update.requires_replay}</p>"
        f"<p>Snapshot ile tutarlı: {update.reconciliation_consistent}</p>"
        f"<h2>Sorunlar</h2><ul>{issues}</ul>"
        "</body></html>"
    )
