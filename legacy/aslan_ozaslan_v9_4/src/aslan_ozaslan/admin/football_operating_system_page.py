from __future__ import annotations
import html

def render_football_operating_system_page(decision, expert_decisions) -> str:
    rows = "".join(
        "<tr>"
        f"<td>{html.escape(item.expert)}</td>"
        f"<td>{html.escape(item.category)}</td>"
        f"<td>{html.escape(item.recommendation)}</td>"
        f"<td>{item.confidence:.3f}</td>"
        f"<td>{item.risk:.3f}</td>"
        f"<td>{html.escape(item.rationale)}</td>"
        "</tr>"
        for item in expert_decisions
    )
    dissent = "".join(
        f"<li>{html.escape(item)}</li>"
        for item in decision.dissenting_experts
    ) or "<li>Yok</li>"

    return (
        "<!doctype html><html lang='tr'><head><meta charset='utf-8'>"
        "<title>Aslan Özaslan Football OS</title></head><body>"
        "<h1>Football Operating System</h1>"
        f"<p>Konu: {html.escape(decision.subject_id)}</p>"
        f"<p>Final öneri: {html.escape(decision.final_recommendation)}</p>"
        f"<p>Güven: {decision.confidence:.3f}</p>"
        f"<p>Risk: {decision.risk:.3f}</p>"
        f"<p>Consensus: {decision.consensus_score:.3f}</p>"
        f"<p>Onaylandı: {decision.approved}</p>"
        f"<h2>Karşı görüşler</h2><ul>{dissent}</ul>"
        "<h2>Uzman kararları</h2>"
        "<table><thead><tr><th>Uzman</th><th>Kategori</th>"
        "<th>Öneri</th><th>Güven</th><th>Risk</th>"
        "<th>Gerekçe</th></tr></thead>"
        f"<tbody>{rows}</tbody></table>"
        "</body></html>"
    )
