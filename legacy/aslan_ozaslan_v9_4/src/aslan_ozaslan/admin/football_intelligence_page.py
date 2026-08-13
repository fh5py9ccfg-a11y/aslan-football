from __future__ import annotations
import html

def render_football_intelligence_page(opinions, recommendation) -> str:
    rows = "".join(
        "<tr>"
        f"<td>{html.escape(opinion.agent_name)}</td>"
        f"<td>{html.escape(opinion.recommendation)}</td>"
        f"<td>{opinion.confidence:.3f}</td>"
        f"<td>{opinion.risk:.3f}</td>"
        f"<td>{html.escape(opinion.rationale)}</td>"
        "</tr>"
        for opinion in opinions
    )
    rationale = "".join(
        f"<li>{html.escape(item)}</li>"
        for item in recommendation.rationale
    ) or "<li>Yok</li>"

    return (
        "<!doctype html><html lang='tr'><head><meta charset='utf-8'>"
        "<title>Aslan Özaslan Football Intelligence</title></head><body>"
        "<h1>AI Football Intelligence</h1>"
        f"<p>Öneri: {html.escape(recommendation.action)}</p>"
        f"<p>Güven: {recommendation.confidence:.3f}</p>"
        f"<p>Risk: {recommendation.risk:.3f}</p>"
        f"<p>Aciliyet: {html.escape(recommendation.urgency)}</p>"
        f"<p>Onaylandı: {recommendation.approved}</p>"
        f"<h2>Gerekçeler</h2><ul>{rationale}</ul>"
        "<h2>Uzman ajan görüşleri</h2>"
        "<table><thead><tr><th>Ajan</th><th>Öneri</th><th>Güven</th>"
        "<th>Risk</th><th>Gerekçe</th></tr></thead>"
        f"<tbody>{rows}</tbody></table>"
        "</body></html>"
    )
