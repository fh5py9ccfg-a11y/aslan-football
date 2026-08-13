from __future__ import annotations

import html


def render_security_page(*, provenance_ok: bool, scan_report, supply_chain_report) -> str:
    finding_rows = "".join(
        "<tr>"
        f"<td>{html.escape(finding.package)}</td>"
        f"<td>{html.escape(finding.severity)}</td>"
        f"<td>{html.escape(finding.fixed_version or '')}</td>"
        "</tr>"
        for finding in scan_report.findings
    )

    blockers = "".join(
        f"<li>{html.escape(item)}</li>"
        for item in supply_chain_report.blockers
    ) or "<li>Yok</li>"

    return (
        "<!doctype html><html lang='tr'><head><meta charset='utf-8'>"
        "<title>Aslan Özaslan Güvenlik</title></head><body>"
        "<h1>Release Güvenliği</h1>"
        f"<p>Provenance: {'Doğrulandı' if provenance_ok else 'Başarısız'}</p>"
        f"<p>Release gate: {'Açık' if supply_chain_report.allowed and provenance_ok else 'Kapalı'}</p>"
        "<h2>Blocker</h2><ul>"
        f"{blockers}</ul>"
        "<h2>Scanner Bulguları</h2><table><tbody>"
        f"{finding_rows}</tbody></table>"
        "</body></html>"
    )
