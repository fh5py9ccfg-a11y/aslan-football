import html
def render_admin_snapshot(snapshot):
    champion=html.escape(snapshot.champion_model or 'Yok')
    ready='Hazır' if snapshot.release_ready else 'Hazır değil'
    return f'<section><h2>Operasyon Özeti</h2><p>Sağlayıcı: {html.escape(snapshot.provider_status)}</p><p>Şampiyon model: {champion}</p><p>Bekleyen fikstür: {snapshot.pending_fixtures}</p><p>Sonuçlandırılmamış tahmin: {snapshot.unsettled_predictions}</p><p>Drift alarmı: {snapshot.drift_alerts}</p><p>Yayın durumu: {ready}</p></section>'
