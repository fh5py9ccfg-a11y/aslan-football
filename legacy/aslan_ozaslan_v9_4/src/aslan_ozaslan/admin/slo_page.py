from __future__ import annotations

import html


def render_slo_page(evaluations) -> str:
    rows = "".join(
        "<tr>"
        f"<td>{html.escape(item.name)}</td>"
        f"<td>{item.achieved * 100:.3f}%</td>"
        f"<td>{item.target * 100:.3f}%</td>"
        f"<td>{'OK' if item.met else 'FAIL'}</td>"
        f"<td>{item.error_budget_remaining * 100:.4f}%</td>"
        "</tr>"
        for item in evaluations
    )

    return (
        "<!doctype html><html lang='tr'><head><meta charset='utf-8'>"
        "<title>Aslan Özaslan SLO</title></head><body>"
        "<h1>Servis Seviyesi Hedefleri</h1>"
        "<table><thead><tr>"
        "<th>Hedef</th><th>Gerçekleşen</th><th>Hedef</th>"
        "<th>Durum</th><th>Kalan hata bütçesi</th>"
        "</tr></thead><tbody>"
        f"{rows}</tbody></table>"
        "</body></html>"
    )
