from __future__ import annotations

def render_model_validation_page(backtest, calibration) -> str:
    return (
        "<!doctype html><html lang='tr'><head><meta charset='utf-8'>"
        "<title>Aslan Özaslan Model Doğrulama</title></head><body>"
        "<h1>Futbol Model Doğrulama</h1>"
        f"<p>Örnek sayısı: {backtest.samples}</p>"
        f"<p>Doğruluk: {backtest.accuracy:.4f}</p>"
        f"<p>Brier skoru: {backtest.brier_score:.4f}</p>"
        f"<p>Log loss: {backtest.log_loss:.4f}</p>"
        f"<p>Calibration error: {calibration.expected_calibration_error:.4f}</p>"
        "</body></html>"
    )
