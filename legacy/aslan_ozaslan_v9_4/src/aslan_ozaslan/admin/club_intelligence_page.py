from __future__ import annotations
import html

def render_club_intelligence_page(
    squad_report,
    budget_assessment,
    advice,
) -> str:
    items = "".join(
        f"<li>{html.escape(item)}</li>"
        for item in advice
    )

    return (
        "<!doctype html><html lang='tr'><head><meta charset='utf-8'>"
        "<title>Aslan Özaslan Club Intelligence</title></head><body>"
        "<h1>Club Intelligence & Squad Planning</h1>"
        f"<p>Kadro büyüklüğü: {squad_report.squad_size}</p>"
        f"<p>Ortalama yaş: {squad_report.average_age:.2f}</p>"
        f"<p>Toplam maaş: {squad_report.total_salary:.2f}</p>"
        f"<p>Toplam piyasa değeri: {squad_report.total_market_value:.2f}</p>"
        f"<p>Kadro derinliği: {squad_report.depth_score:.3f}</p>"
        f"<p>Yaş dengesi: {squad_report.age_balance_score:.3f}</p>"
        f"<p>Sözleşme riski: {squad_report.contract_risk_score:.3f}</p>"
        f"<p>Maaş bütçesi durumu: {html.escape(budget_assessment.status)}</p>"
        f"<p>Maaş kullanım oranı: {budget_assessment.salary_utilization:.3f}</p>"
        f"<h2>Club AI Advisor</h2><ul>{items}</ul>"
        "</body></html>"
    )
