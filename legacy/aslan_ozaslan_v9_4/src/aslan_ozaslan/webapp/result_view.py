from __future__ import annotations
import html

def render_prediction_result(record) -> str:
    if record is None:
        return "<p>Bu maç için analiz bulunamadı.</p>"

    if record.status != "OK":
        warnings = "".join("<li>%s</li>" % html.escape(item) for item in record.warnings)
        return "<section><h2>Analiz çalıştırılmadı</h2><ul>%s</ul></section>" % warnings

    rows = (
        ("Ev sahibi", record.home_probability),
        ("Beraberlik", record.draw_probability),
        ("Deplasman", record.away_probability),
    )
    probability_html = "".join(
        "<li><strong>%s</strong>: %%%.1f</li>" % (label, value * 100)
        for label, value in rows
    )
    warnings = "".join("<li>%s</li>" % html.escape(item) for item in record.warnings)
    return (
        "<section><h2>Analiz sonucu</h2><ul>%s</ul>"
        "<p>Beklenen gol: %.2f - %.2f</p>"
        "<p>Veri güveni: %d/100</p>"
        "<p>Model sürümü: %s</p><ul>%s</ul></section>"
    ) % (
        probability_html,
        record.home_expected_goals,
        record.away_expected_goals,
        record.data_confidence,
        html.escape(record.model_version),
        warnings,
    )
