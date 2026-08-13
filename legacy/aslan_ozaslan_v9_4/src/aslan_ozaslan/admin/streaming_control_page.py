from __future__ import annotations
import html

def render_streaming_control_page(checkpoint, recovery, active_events) -> str:
    rows = "".join(
        "<tr>"
        f"<td>{html.escape(event.event_id)}</td>"
        f"<td>{event.version}</td>"
        f"<td>{'ACTIVE' if event.active else 'INACTIVE'}</td>"
        "</tr>"
        for event in active_events
    ) or "<tr><td colspan='3'>Aktif event yok</td></tr>"

    return (
        "<!doctype html><html lang='tr'><head><meta charset='utf-8'>"
        "<title>Aslan Özaslan Streaming Control</title></head><body>"
        "<h1>Streaming Control Center</h1>"
        f"<p>Stream: {html.escape(checkpoint.stream_id)}</p>"
        f"<p>Son sequence: {checkpoint.last_sequence}</p>"
        f"<p>İşlenen event: {checkpoint.processed_events}</p>"
        f"<p>Düzeltme: {checkpoint.corrected_events}</p>"
        f"<p>Devam sequence: {recovery.resume_from_sequence}</p>"
        f"<p>Replay gerekli: {recovery.replay_required}</p>"
        "<h2>Aktif event ledger</h2>"
        "<table><thead><tr><th>Event</th><th>Versiyon</th>"
        "<th>Durum</th></tr></thead>"
        f"<tbody>{rows}</tbody></table>"
        "</body></html>"
    )
