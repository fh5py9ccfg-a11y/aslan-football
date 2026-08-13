from __future__ import annotations
import html

def render_outbox_operations_page(outbox, worker_report) -> str:
    statuses = (
        "PENDING",
        "PROCESSING",
        "RETRY",
        "PUBLISHED",
        "DEAD_LETTER",
    )
    rows = "".join(
        "<tr>"
        f"<td>{html.escape(status)}</td>"
        f"<td>{len(outbox.list_by_status(status))}</td>"
        "</tr>"
        for status in statuses
    )

    return (
        "<!doctype html><html lang='tr'><head><meta charset='utf-8'>"
        "<title>Aslan Özaslan Outbox Operations</title></head><body>"
        "<h1>Transactional Outbox Operations</h1>"
        f"<p>Worker: {html.escape(worker_report.worker_id)}</p>"
        f"<p>Claimed: {worker_report.claimed}</p>"
        f"<p>Published: {worker_report.published}</p>"
        f"<p>Retried: {worker_report.retried}</p>"
        f"<p>Dead letter: {worker_report.dead_lettered}</p>"
        "<table><thead><tr><th>Durum</th><th>Adet</th></tr></thead>"
        f"<tbody>{rows}</tbody></table>"
        "</body></html>"
    )
