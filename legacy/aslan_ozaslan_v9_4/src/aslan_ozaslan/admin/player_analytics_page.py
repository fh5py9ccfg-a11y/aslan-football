from __future__ import annotations
import html

def render_player_analytics_page(player, score, trend) -> str:
    return (
        "<!doctype html><html lang='tr'><head><meta charset='utf-8'>"
        "<title>Aslan Özaslan Oyuncu Analizi</title></head><body>"
        f"<h1>{html.escape(player.name)} Oyuncu Analizi</h1>"
        f"<p>Pozisyon: {html.escape(player.position)}</p>"
        f"<p>Genel değer: {score.overall:.2f}</p>"
        f"<p>Hücum: {score.attacking:.2f}</p>"
        f"<p>Yaratıcılık: {score.creativity:.2f}</p>"
        f"<p>İlerletme: {score.progression:.2f}</p>"
        f"<p>Savunma: {score.defensive:.2f}</p>"
        f"<p>Pres: {score.pressing:.2f}</p>"
        f"<p>Güvenilirlik: {score.reliability:.2f}</p>"
        f"<p>Form trendi: {html.escape(trend.trend)}</p>"
        "</body></html>"
    )
