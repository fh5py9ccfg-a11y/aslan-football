from __future__ import annotations
import html

def render_matchup_page(assessment) -> str:
    reasons = "".join(f"<li>{html.escape(x)}</li>" for x in assessment.explanation)
    return (
        "<!doctype html><html lang='tr'><head><meta charset='utf-8'>"
        "<title>Aslan Özaslan Maç Analizi</title></head><body>"
        "<h1>Maç Eşleşme Analizi</h1>"
        f"<p>Avantaj: {html.escape(assessment.edge)}</p>"
        f"<p>Güven: {assessment.confidence:.2f}</p>"
        f"<p>Ev gücü: {assessment.home_strength:.1f}</p>"
        f"<p>Deplasman gücü: {assessment.away_strength:.1f}</p>"
        f"<h2>Açıklama</h2><ul>{reasons}</ul></body></html>"
    )
