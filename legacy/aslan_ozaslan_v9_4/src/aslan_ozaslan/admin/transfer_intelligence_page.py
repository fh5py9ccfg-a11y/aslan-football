from __future__ import annotations
import html

def render_transfer_intelligence_page(profile, assessment) -> str:
    warnings = "".join(
        f"<li>{html.escape(item)}</li>"
        for item in assessment.warnings
    ) or "<li>Yok</li>"

    return (
        "<!doctype html><html lang='tr'><head><meta charset='utf-8'>"
        "<title>Aslan Özaslan Transfer Intelligence</title></head><body>"
        "<h1>Transfer Intelligence</h1>"
        f"<p>Oyuncu: {html.escape(profile.name)}</p>"
        f"<p>Pozisyon: {html.escape(profile.position)}</p>"
        f"<p>Yaş: {profile.age}</p>"
        f"<p>Genel skor: {assessment.overall_score:.3f}</p>"
        f"<p>Performans: {assessment.performance_score:.3f}</p>"
        f"<p>Yaş eğrisi: {assessment.age_curve_score:.3f}</p>"
        f"<p>Sakatlık riski: {assessment.injury_risk_score:.3f}</p>"
        f"<p>Maliyet verimi: {assessment.cost_efficiency_score:.3f}</p>"
        f"<p>Sözleşme avantajı: {assessment.contract_leverage_score:.3f}</p>"
        f"<p>Öneri: {html.escape(assessment.recommendation)}</p>"
        f"<h2>Uyarılar</h2><ul>{warnings}</ul>"
        "</body></html>"
    )
