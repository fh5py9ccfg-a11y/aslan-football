from __future__ import annotations
import html

def render_provider_connection_page(status) -> str:
    return (
        "<!doctype html><html lang='tr'><head><meta charset='utf-8'>"
        "<title>Aslan Özaslan Veri Kaynakları</title></head><body>"
        "<h1>Veri Kaynağı Bağlantıları</h1>"
        f"<p>Sağlayıcı: {html.escape(status.provider)}</p>"
        f"<p>Durum: {html.escape(status.label)}</p>"
        f"<p>Bağlı: {status.connected}</p>"
        f"<p>Dış istek izni: {status.request_allowed}</p>"
        "</body></html>"
    )
