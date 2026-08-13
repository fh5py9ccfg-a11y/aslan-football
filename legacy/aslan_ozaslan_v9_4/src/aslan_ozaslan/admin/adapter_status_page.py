from __future__ import annotations
import html

def render_adapter_status_page(registry, weights) -> str:
    rows = "".join(
        "<tr>"
        f"<td>{html.escape(name)}</td>"
        f"<td>{weights.get(name, 1.0):.2f}</td>"
        "<td>READY</td>"
        "</tr>"
        for name in registry.names()
    )
    return (
        "<!doctype html><html lang='tr'><head><meta charset='utf-8'>"
        "<title>Aslan Özaslan Expert Adapters</title></head><body>"
        "<h1>Football OS Expert Adapters</h1>"
        "<table><thead><tr><th>Adapter</th><th>Ağırlık</th>"
        "<th>Durum</th></tr></thead>"
        f"<tbody>{rows}</tbody></table>"
        "</body></html>"
    )
