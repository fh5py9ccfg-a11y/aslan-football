from __future__ import annotations

def render_match_simulation_page(report, comparison=None) -> str:
    comparison_html = ""
    if comparison is not None:
        comparison_html = (
            "<h2>Senaryo farkı</h2>"
            f"<p>Ev kazanma değişimi: {comparison.home_win_change:+.3f}</p>"
            f"<p>Beraberlik değişimi: {comparison.draw_change:+.3f}</p>"
            f"<p>Deplasman kazanma değişimi: {comparison.away_win_change:+.3f}</p>"
        )

    return (
        "<!doctype html><html lang='tr'><head><meta charset='utf-8'>"
        "<title>Aslan Özaslan Maç Simülasyonu</title></head><body>"
        "<h1>Monte Carlo Maç Simülasyonu</h1>"
        f"<p>Simülasyon sayısı: {report.iterations}</p>"
        f"<p>Ev kazanır: {report.home_win_probability:.3f}</p>"
        f"<p>Beraberlik: {report.draw_probability:.3f}</p>"
        f"<p>Deplasman kazanır: {report.away_win_probability:.3f}</p>"
        f"<p>Ortalama gol: {report.average_home_goals:.2f} - "
        f"{report.average_away_goals:.2f}</p>"
        f"<p>En sık skor: {report.most_common_score[0]} - "
        f"{report.most_common_score[1]}</p>"
        f"{comparison_html}</body></html>"
    )
