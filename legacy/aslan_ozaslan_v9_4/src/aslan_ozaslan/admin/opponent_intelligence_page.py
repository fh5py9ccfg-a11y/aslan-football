from __future__ import annotations
import html

def render_opponent_intelligence_page(report) -> str:
    matchups = "".join(
        f"<li>{html.escape(item)}</li>"
        for item in report.critical_matchups
    ) or "<li>Yok</li>"
    plans = "".join(
        "<tr>"
        f"<td>{html.escape(plan.name)}</td>"
        f"<td>{plan.pressing_level:.2f}</td>"
        f"<td>{plan.width:.2f}</td>"
        f"<td>{plan.tempo:.2f}</td>"
        f"<td>{html.escape(plan.primary_zone)}</td>"
        "</tr>"
        for plan in report.plans
    )

    return (
        "<!doctype html><html lang='tr'><head><meta charset='utf-8'>"
        "<title>Aslan Özaslan Opponent Intelligence</title></head><body>"
        "<h1>Opponent Intelligence & Match Preparation</h1>"
        f"<p>Rakip: {html.escape(report.opponent_id)}</p>"
        f"<p>Önerilen plan: {html.escape(report.recommended_plan)}</p>"
        f"<p>{html.escape(report.briefing)}</p>"
        "<h2>Zayıf bölgeler</h2>"
        f"<p>Sol: {report.weakness_map.left_defense:.3f}</p>"
        f"<p>Sağ: {report.weakness_map.right_defense:.3f}</p>"
        f"<p>Merkez: {report.weakness_map.central_defense:.3f}</p>"
        f"<p>Geçiş: {report.weakness_map.transition_defense:.3f}</p>"
        f"<p>Duran top: {report.weakness_map.set_piece_defense:.3f}</p>"
        f"<h2>Kritik eşleşmeler</h2><ul>{matchups}</ul>"
        "<h2>Maç planları</h2>"
        "<table><thead><tr><th>Plan</th><th>Pres</th><th>Genişlik</th>"
        "<th>Tempo</th><th>Ana bölge</th></tr></thead>"
        f"<tbody>{plans}</tbody></table>"
        "</body></html>"
    )
