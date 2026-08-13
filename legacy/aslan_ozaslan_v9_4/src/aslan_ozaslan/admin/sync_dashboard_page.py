import html
def render_sync_dashboard_page(report):
    errors=''.join(f'<li>{html.escape(x)}</li>' for x in report.integrity_errors) or '<li>Yok</li>'
    return ("<!doctype html><html lang='tr'><head><meta charset='utf-8'><title>Aslan Özaslan Sync Dashboard</title></head><body>"
            "<h1>Production Data Sync</h1>"+f"<p>Tamamlandı: {report.completed}</p><p>Sayfa: {report.cursor.page}</p>"
            +f"<p>İstek: {report.metrics.requests}</p><p>Başarılı: {report.metrics.successes}</p><p>Başarısız: {report.metrics.failures}</p>"
            +f"<p>Görülen fixture: {report.metrics.fixtures_seen}</p><p>Güncellenen fixture: {report.metrics.fixtures_updated}</p><p>Atlanan fixture: {report.metrics.fixtures_skipped}</p>"
            +f"<p>Ortalama gecikme: {report.metrics.average_latency_ms:.2f} ms</p><h2>Bütünlük hataları</h2><ul>{errors}</ul></body></html>")
