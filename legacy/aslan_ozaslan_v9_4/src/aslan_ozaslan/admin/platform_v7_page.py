from __future__ import annotations
import html

def render_platform_v7_page(status, release_decision) -> str:
    blockers = "".join(
        f"<li>{html.escape(item)}</li>"
        for item in release_decision.blockers
    ) or "<li>Yok</li>"
    warnings = "".join(
        f"<li>{html.escape(item)}</li>"
        for item in release_decision.warnings
    ) or "<li>Yok</li>"

    return (
        "<!doctype html><html lang='tr'><head><meta charset='utf-8'>"
        "<title>Aslan Özaslan v7.0</title></head><body>"
        "<h1>Aslan Özaslan v7.0 Release Candidate</h1>"
        f"<p>Sürüm: {html.escape(status.version)}</p>"
        f"<p>Production ready: {status.production_ready}</p>"
        f"<p>Safe mode: {status.safe_mode}</p>"
        f"<p>Test sayısı: {status.test_count}</p>"
        f"<p>Aktif fixture: {status.active_fixture_count}</p>"
        f"<p>Provider bağlı: {status.provider_connected}</p>"
        f"<p>Release onayı: {release_decision.approved}</p>"
        f"<h2>Blocker</h2><ul>{blockers}</ul>"
        f"<h2>Uyarılar</h2><ul>{warnings}</ul>"
        "</body></html>"
    )
