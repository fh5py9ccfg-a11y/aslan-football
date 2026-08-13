from __future__ import annotations
import html

def render_promotion_page(decision) -> str:
    blockers = "".join(
        f"<li>{html.escape(item)}</li>" for item in decision.blockers
    ) or "<li>Yok</li>"
    warnings = "".join(
        f"<li>{html.escape(item)}</li>" for item in decision.warnings
    ) or "<li>Yok</li>"

    return (
        "<!doctype html><html lang='tr'><head><meta charset='utf-8'>"
        "<title>Aslan Özaslan Model Promotion</title></head><body>"
        "<h1>Futbol Model Promotion Kararı</h1>"
        f"<p>Durum: {'Onaylandı' if decision.allowed else 'Engellendi'}</p>"
        f"<h2>Blocker</h2><ul>{blockers}</ul>"
        f"<h2>Uyarılar</h2><ul>{warnings}</ul>"
        "</body></html>"
    )
