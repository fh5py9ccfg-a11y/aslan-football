from __future__ import annotations

import html


def render_release_page(*, readiness_report, smoke_report, artifact=None) -> str:
    artifact_html = (
        "<p>Henüz release artifact oluşturulmadı.</p>"
        if artifact is None
        else (
            f"<p>Sürüm: {html.escape(artifact.version)}</p>"
            f"<p>SHA-256: {html.escape(artifact.sha256)}</p>"
        )
    )

    blockers = "".join(
        f"<li>{html.escape(name)}</li>"
        for name in readiness_report.blockers
    ) or "<li>Yok</li>"

    smoke_rows = "".join(
        "<tr>"
        f"<td>{html.escape(check.name)}</td>"
        f"<td>{'OK' if check.passed else 'FAIL'}</td>"
        f"<td>{html.escape(check.detail)}</td>"
        "</tr>"
        for check in smoke_report.checks
    )

    return (
        "<!doctype html><html lang='tr'><head><meta charset='utf-8'>"
        "<title>Aslan Özaslan Release</title></head><body>"
        "<h1>Release Kontrolü</h1>"
        f"<p>Hazırlık skoru: {readiness_report.score}/100</p>"
        f"<p>Release durumu: {'Hazır' if readiness_report.ready and smoke_report.passed else 'Hazır değil'}</p>"
        "<h2>Blocker</h2><ul>"
        f"{blockers}</ul>"
        "<h2>Smoke Testleri</h2><table><tbody>"
        f"{smoke_rows}</tbody></table>"
        "<h2>Artifact</h2>"
        f"{artifact_html}"
        "</body></html>"
    )
