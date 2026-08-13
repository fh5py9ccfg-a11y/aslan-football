from __future__ import annotations


def render_control_center_page(snapshot) -> str:
    def state(value: bool) -> str:
        return "OK" if value else "FAIL"

    return (
        "<!doctype html><html lang='tr'><head><meta charset='utf-8'>"
        "<title>Aslan Özaslan Kontrol Merkezi</title></head><body>"
        "<h1>Production Operasyon Kontrol Merkezi</h1>"
        f"<p>Genel release durumu: {'Hazır' if snapshot.release_ready else 'Hazır değil'}</p>"
        "<ul>"
        f"<li>Sistem sağlığı: {state(snapshot.health_ok)}</li>"
        f"<li>Audit zinciri: {state(snapshot.audit_chain_ok)}</li>"
        f"<li>Sertifika alarmı: {snapshot.certificate_alerts}</li>"
        f"<li>Dead-letter işi: {snapshot.dead_letter_jobs}</li>"
        f"<li>Drift alarmı: {snapshot.drift_alerts}</li>"
        f"<li>Release onayı: {state(snapshot.release_approved)}</li>"
        "</ul>"
        "</body></html>"
    )
