from __future__ import annotations

import html


def render_policy_page(decision) -> str:
    blockers = "".join(
        f"<li>{html.escape(item)}</li>"
        for item in decision.blockers
    ) or "<li>Yok</li>"

    warnings = "".join(
        f"<li>{html.escape(item)}</li>"
        for item in decision.warnings
    ) or "<li>Yok</li>"

    return (
        "<!doctype html><html lang='tr'><head><meta charset='utf-8'>"
        "<title>Aslan Özaslan Policy</title></head><body>"
        "<h1>Deployment Policy Sonucu</h1>"
        f"<p>Durum: {'İzin verildi' if decision.allowed else 'Engellendi'}</p>"
        "<h2>Blocker</h2><ul>"
        f"{blockers}</ul>"
        "<h2>Uyarılar</h2><ul>"
        f"{warnings}</ul>"
        "</body></html>"
    )
