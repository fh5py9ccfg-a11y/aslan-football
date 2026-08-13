from __future__ import annotations

import html


def render_operations_page(
    *,
    metrics: dict[str, float],
    dead_letters,
    health_report,
) -> str:
    metric_rows = "".join(
        f"<tr><td>{html.escape(name)}</td><td>{value}</td></tr>"
        for name, value in sorted(metrics.items())
    )
    dead_rows = "".join(
        "<tr>"
        f"<td>{html.escape(job.job_id)}</td>"
        f"<td>{html.escape(job.name)}</td>"
        f"<td>{job.attempts}</td>"
        f"<td>{html.escape(job.error or '')}</td>"
        "</tr>"
        for job in dead_letters
    )
    health_rows = "".join(
        "<tr>"
        f"<td>{html.escape(check.name)}</td>"
        f"<td>{'OK' if check.healthy else 'FAIL'}</td>"
        f"<td>{'Kritik' if check.critical else 'İkincil'}</td>"
        f"<td>{html.escape(check.message)}</td>"
        "</tr>"
        for check in health_report.checks
    )
    return (
        "<!doctype html><html lang='tr'><head><meta charset='utf-8'>"
        "<title>Aslan Özaslan Operasyon</title></head><body>"
        "<h1>Operasyon Paneli</h1>"
        f"<p>Genel sağlık: {'Sağlıklı' if health_report.healthy else 'Hazır değil'}</p>"
        "<h2>Metrikler</h2><table><tbody>"
        f"{metric_rows}</tbody></table>"
        "<h2>Sağlık Kontrolleri</h2><table><tbody>"
        f"{health_rows}</tbody></table>"
        "<h2>Dead-letter İşleri</h2><table><tbody>"
        f"{dead_rows}</tbody></table>"
        "</body></html>"
    )
