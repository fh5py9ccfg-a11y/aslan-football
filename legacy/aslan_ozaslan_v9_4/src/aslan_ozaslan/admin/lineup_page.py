import html

def render_lineup_page(selection, recommendation):
    starters = "".join(f"<li>{html.escape(x)}</li>" for x in selection.player_ids)
    resting = "".join(f"<li>{html.escape(x)}</li>" for x in recommendation.rest_player_ids) or "<li>Yok</li>"
    return (
        "<!doctype html><html lang='tr'><head><meta charset='utf-8'>"
        "<title>Aslan Özaslan İlk 11</title></head><body>"
        "<h1>Kadro ve İlk 11 Analizi</h1>"
        f"<p>Objektif skor: {selection.objective_score:.2f}</p>"
        f"<p>Chemistry: {selection.chemistry_score:.3f}</p>"
        f"<p>Yorgunluk cezası: {selection.fatigue_penalty:.3f}</p>"
        f"<h2>Seçilen oyuncular</h2><ul>{starters}</ul>"
        f"<h2>Dinlendirme önerisi</h2><ul>{resting}</ul>"
        f"<p>{html.escape(recommendation.reason)}</p></body></html>"
    )
