import html
def render_event_sourcing_page(replay, verification):
    mismatches = "".join(
        f"<li>{html.escape(x)}</li>" for x in verification.mismatches
    ) or "<li>Yok</li>"
    return (
        "<!doctype html><html lang='tr'><head><meta charset='utf-8'>"
        "<title>Aslan Özaslan Event Sourcing</title></head><body>"
        "<h1>Event Sourcing & Replay</h1>"
        f"<p>Fixture: {html.escape(replay.state.fixture_id)}</p>"
        f"<p>Son sequence: {replay.state.last_sequence}</p>"
        f"<p>Skor: {replay.state.home_goals} - {replay.state.away_goals}</p>"
        f"<p>Dakika: {replay.state.minute}</p>"
        f"<p>Replay event sayısı: {replay.replayed_events}</p>"
        f"<p>Snapshot kullanıldı: {replay.used_snapshot}</p>"
        f"<p>Replay süresi: {replay.duration_ms:.2f} ms</p>"
        f"<p>Doğrulama: {verification.valid}</p>"
        f"<h2>Uyuşmazlıklar</h2><ul>{mismatches}</ul></body></html>"
    )
