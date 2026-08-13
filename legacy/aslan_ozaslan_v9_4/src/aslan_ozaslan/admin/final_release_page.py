from __future__ import annotations
import html

def render_final_release_page(decision, smoke_report, environment_report) -> str:
    blockers = "".join(
        f"<li>{html.escape(item)}</li>" for item in decision.blockers
    ) or "<li>Yok</li>"
    warnings = "".join(
        f"<li>{html.escape(item)}</li>" for item in decision.warnings
    ) or "<li>Yok</li>"
    checks = "".join(
        "<tr>"
        f"<td>{html.escape(check.name)}</td>"
        f"<td>{check.passed}</td>"
        f"<td>{check.latency_ms:.2f}</td>"
        f"<td>{html.escape(check.detail)}</td>"
        "</tr>"
        for check in smoke_report.checks
    )

    return (
        "<!doctype html><html lang='tr'><head><meta charset='utf-8'>"
        "<title>Aslan Özaslan Final Release</title></head><body>"
        "<h1>Final v7 Release Validation</h1>"
        f"<p>Karar: {decision.approved}</p>"
        f"<p>Sürüm: {html.escape(decision.version)}</p>"
        f"<p>Environment ready: {environment_report.ready}</p>"
        f"<p>Provider verified: {smoke_report.provider_verified}</p>"
        f"<h2>Blocker</h2><ul>{blockers}</ul>"
        f"<h2>Uyarılar</h2><ul>{warnings}</ul>"
        "<h2>Smoke testleri</h2>"
        "<table><thead><tr><th>Kontrol</th><th>Başarılı</th>"
        "<th>Gecikme</th><th>Detay</th></tr></thead>"
        f"<tbody>{checks}</tbody></table>"
        "</body></html>"
    )
