from __future__ import annotations
import html

def render_season_projection_page(projections) -> str:
    rows = "".join(
        "<tr>"
        f"<td>{html.escape(item.team_id)}</td>"
        f"<td>{item.average_points:.2f}</td>"
        f"<td>{item.title_probability:.3f}</td>"
        f"<td>{item.top_four_probability:.3f}</td>"
        f"<td>{item.relegation_probability:.3f}</td>"
        "</tr>"
        for item in projections
    )
    return (
        "<!doctype html><html lang='tr'><head><meta charset='utf-8'>"
        "<title>Aslan Özaslan Sezon Projeksiyonu</title></head><body>"
        "<h1>Monte Carlo Sezon Projeksiyonu</h1>"
        "<table><thead><tr>"
        "<th>Takım</th><th>Ortalama puan</th><th>Şampiyonluk</th>"
        "<th>İlk 4</th><th>Düşme</th>"
        "</tr></thead><tbody>"
        f"{rows}</tbody></table>"
        "</body></html>"
    )
