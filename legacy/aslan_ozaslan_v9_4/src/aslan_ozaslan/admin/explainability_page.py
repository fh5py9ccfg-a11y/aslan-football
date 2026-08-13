from __future__ import annotations
import html

def render_explainability_page(report) -> str:
    rows = "".join(
        "<tr>"
        f"<td>{html.escape(factor.name)}</td>"
        f"<td>{factor.signed_share * 100:+.1f}%</td>"
        f"<td>{factor.confidence:.2f}</td>"
        f"<td>{html.escape(factor.category)}</td>"
        "</tr>"
        for factor in report.factors
    )

    warnings = "".join(
        f"<li>{html.escape(item)}</li>"
        for item in report.reliability.warnings
    ) or "<li>Yok</li>"

    return (
        "<!doctype html><html lang='tr'><head><meta charset='utf-8'>"
        "<title>Aslan Özaslan Açıklanabilir Tahmin</title></head><body>"
        "<h1>Explainable Football AI</h1>"
        f"<p>Sonuç: {html.escape(report.outcome)}</p>"
        f"<p>Olasılık: {report.probability:.3f}</p>"
        f"<p>Model fikir birliği: {report.consensus.consensus_score:.3f}</p>"
        f"<p>Güvenilirlik: {html.escape(report.reliability.label)} "
        f"({report.reliability.score:.3f})</p>"
        f"<p>{html.escape(report.narrative)}</p>"
        "<h2>Faktör katkıları</h2>"
        "<table><thead><tr><th>Faktör</th><th>Katkı</th>"
        "<th>Faktör güveni</th><th>Kategori</th></tr></thead>"
        f"<tbody>{rows}</tbody></table>"
        f"<h2>Uyarılar</h2><ul>{warnings}</ul>"
        "</body></html>"
    )
