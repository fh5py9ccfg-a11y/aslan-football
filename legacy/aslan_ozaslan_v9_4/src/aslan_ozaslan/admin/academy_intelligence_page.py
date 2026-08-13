from __future__ import annotations
import html

def render_academy_intelligence_page(player, assessment, narrative) -> str:
    risks = "".join(
        f"<li>{html.escape(item)}</li>"
        for item in assessment.risks
    ) or "<li>Yok</li>"

    return (
        "<!doctype html><html lang='tr'><head><meta charset='utf-8'>"
        "<title>Aslan Özaslan Academy Intelligence</title></head><body>"
        "<h1>Academy Intelligence</h1>"
        f"<p>Oyuncu: {html.escape(player.name)}</p>"
        f"<p>Yaş: {player.age}</p>"
        f"<p>Pozisyon: {html.escape(player.position)}</p>"
        f"<p>Gelişim skoru: {assessment.development_score:.3f}</p>"
        f"<p>A takım hazırlığı: {assessment.first_team_readiness:.3f}</p>"
        f"<p>Kiralık uygunluğu: {assessment.loan_suitability:.3f}</p>"
        f"<p>12 ay seviye: {assessment.projected_level_12m:.3f}</p>"
        f"<p>24 ay piyasa değeri: {assessment.projected_market_value_24m:.2f}</p>"
        f"<p>Gelişim yolu: {html.escape(assessment.pathway)}</p>"
        f"<p>{html.escape(narrative)}</p>"
        f"<h2>Riskler</h2><ul>{risks}</ul>"
        "</body></html>"
    )
