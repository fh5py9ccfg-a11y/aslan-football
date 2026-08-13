from __future__ import annotations
import html

def render_executive_intelligence_page(report, benchmarks) -> str:
    actions = "".join(
        f"<li>{html.escape(item)}</li>"
        for item in report.priority_actions
    )
    rows = "".join(
        "<tr>"
        f"<td>{html.escape(item.club_id)}</td>"
        f"<td>{item.composite_score:.3f}</td>"
        f"<td>{item.sporting_rank}</td>"
        f"<td>{item.financial_rank}</td>"
        f"<td>{item.overall_rank}</td>"
        "</tr>"
        for item in benchmarks
    )

    return (
        "<!doctype html><html lang='tr'><head><meta charset='utf-8'>"
        "<title>Aslan Özaslan Executive Intelligence</title></head><body>"
        "<h1>Executive Intelligence Center</h1>"
        f"<p>Kulüp: {html.escape(report.club_id)}</p>"
        f"<p>Genel sağlık: {report.health_score:.3f}</p>"
        f"<p>Hedef ilerlemesi: {report.objective_progress:.3f}</p>"
        f"<p>Finansal istikrar: {report.financial_stability:.3f}</p>"
        f"<p>Stratejik risk: {report.strategic_risk:.3f}</p>"
        f"<p>Durum: {html.escape(report.status)}</p>"
        f"<h2>Öncelikli aksiyonlar</h2><ul>{actions}</ul>"
        "<h2>Kulüp karşılaştırması</h2>"
        "<table><thead><tr><th>Kulüp</th><th>Kompozit</th>"
        "<th>Sportif sıra</th><th>Finansal sıra</th>"
        "<th>Genel sıra</th></tr></thead>"
        f"<tbody>{rows}</tbody></table>"
        "</body></html>"
    )
