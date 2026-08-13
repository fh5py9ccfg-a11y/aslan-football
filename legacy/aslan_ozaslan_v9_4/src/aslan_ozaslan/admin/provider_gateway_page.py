from __future__ import annotations
import html

def render_provider_gateway_page(results, quarantine_count: int) -> str:
    rows = "".join(
        "<tr>"
        f"<td>{html.escape(item.payload_type)}</td>"
        f"<td>{item.accepted}</td>"
        f"<td>{html.escape(', '.join(item.errors) or 'Yok')}</td>"
        f"<td>{html.escape(', '.join(item.warnings) or 'Yok')}</td>"
        "</tr>"
        for item in results
    )

    return (
        "<!doctype html><html lang='tr'><head><meta charset='utf-8'>"
        "<title>Aslan Özaslan Provider Gateway</title></head><body>"
        "<h1>Sportmonks Provider Payload Gateway</h1>"
        f"<p>Karantina kayıtları: {quarantine_count}</p>"
        "<table><thead><tr><th>Tür</th><th>Kabul</th>"
        "<th>Hatalar</th><th>Uyarılar</th></tr></thead>"
        f"<tbody>{rows}</tbody></table>"
        "</body></html>"
    )
