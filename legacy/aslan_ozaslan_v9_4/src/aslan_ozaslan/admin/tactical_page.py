import html
def render_tactical_page(report,scenario,compatibility):
    reasons=''.join(f'<li>{html.escape(x)}</li>' for x in report.explanations)
    scenario_reasons=''.join(f'<li>{html.escape(x)}</li>' for x in scenario.explanation)
    return ("<!doctype html><html lang='tr'><head><meta charset='utf-8'><title>Aslan Özaslan Taktik Analiz</title></head><body>"
            "<h1>Taktik Eşleşme Analizi</h1>"+f"<p>Avantaj: {html.escape(report.advantage)}</p><p>Genel taktik fark: {report.overall_edge:+.3f}</p><p>Kadro-taktik uyumu: {compatibility.compatibility_score:.3f}</p><p>Senaryo risk seviyesi: {html.escape(scenario.risk_level)}</p><h2>Eşleşme nedenleri</h2><ul>{reasons}</ul><h2>Senaryo ayarları</h2><ul>{scenario_reasons}</ul></body></html>")
