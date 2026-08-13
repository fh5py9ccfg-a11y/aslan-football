from __future__ import annotations
import html

def render_scout_intelligence_page(assessment, narrative) -> str:
    reasons = "".join(
        f"<li>{html.escape(item)}</li>"
        for item in assessment.reasons
    )

    return (
        "<!doctype html><html lang='tr'><head><meta charset='utf-8'>"
        "<title>Aslan Özaslan Scout Intelligence</title></head><body>"
        "<h1>Scout Intelligence</h1>"
        f"<p>Oyuncu: {html.escape(assessment.player_id)}</p>"
        f"<p>Kulüp uyumu: {assessment.club_fit_score:.3f}</p>"
        f"<p>12 ay projeksiyon: {assessment.projected_level_12m:.3f}</p>"
        f"<p>24 ay projeksiyon: {assessment.projected_level_24m:.3f}</p>"
        f"<p>Lig geçişi: {assessment.league_translation_score:.3f}</p>"
        f"<p>Gizli yetenek: {assessment.hidden_gem_score:.3f}</p>"
        f"<p>Risk: {assessment.risk_score:.3f}</p>"
        f"<p>Öneri: {html.escape(assessment.recommendation)}</p>"
        f"<p>{html.escape(narrative)}</p>"
        f"<h2>Nedenler</h2><ul>{reasons}</ul>"
        "</body></html>"
    )
