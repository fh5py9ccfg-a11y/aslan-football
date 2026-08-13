import html
def render_live_match_page(state,momentum,events):
    rows=''.join(f'<tr><td>{e.minute}</td><td>{html.escape(e.team_id)}</td><td>{html.escape(e.event_type)}</td><td>{e.value:.2f}</td></tr>' for e in events)
    return ("<!doctype html><html lang='tr'><head><meta charset='utf-8'><title>Aslan Özaslan Canlı Maç</title></head><body>"
            "<h1>Canlı Maç Analizi</h1>"
            f'<p>Dakika: {state.minute}</p><p>Skor: {state.home_goals} - {state.away_goals}</p>'
            f'<p>Ev kazanır: {state.home_probability:.3f}</p><p>Beraberlik: {state.draw_probability:.3f}</p><p>Deplasman kazanır: {state.away_probability:.3f}</p>'
            f'<p>Momentum: {html.escape(momentum.dominant_team)} ({momentum.net_momentum:+.2f})</p>'
            "<h2>Olay akışı</h2><table><thead><tr><th>Dakika</th><th>Takım</th><th>Olay</th><th>Değer</th></tr></thead>"
            f'<tbody>{rows}</tbody></table></body></html>')
