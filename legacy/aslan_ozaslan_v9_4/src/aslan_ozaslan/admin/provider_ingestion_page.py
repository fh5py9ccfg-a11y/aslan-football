from __future__ import annotations
import html

def render_provider_ingestion_page(report, archive_count: int) -> str:
    rows = "".join(
        "<tr>"
        f"<td>{html.escape(item.payload_type)}</td>"
        f"<td>{html.escape(item.external_id or 'unknown')}</td>"
        f"<td>{item.accepted}</td>"
        f"<td>{item.duplicate}</td>"
        f"<td>{item.archived}</td>"
        f"<td>{item.projected}</td>"
        f"<td>{item.quarantined}</td>"
        f"<td>{html.escape(item.reason)}</td>"
        "</tr>"
        for item in report.results
    )
    return (
        "<!doctype html><html lang='tr'><head><meta charset='utf-8'>"
        "<title>Aslan Özaslan Provider Ingestion</title></head><body>"
        "<h1>Provider Ingestion Orchestrator</h1>"
        f"<p>Toplam: {report.total}</p>"
        f"<p>Kabul: {report.accepted}</p>"
        f"<p>Duplicate: {report.duplicates}</p>"
        f"<p>Karantina: {report.quarantined}</p>"
        f"<p>Arşiv kayıtları: {archive_count}</p>"
        "<table><thead><tr><th>Tür</th><th>ID</th><th>Kabul</th>"
        "<th>Duplicate</th><th>Arşiv</th><th>Projection</th>"
        "<th>Karantina</th><th>Neden</th></tr></thead>"
        f"<tbody>{rows}</tbody></table>"
        "</body></html>"
    )
