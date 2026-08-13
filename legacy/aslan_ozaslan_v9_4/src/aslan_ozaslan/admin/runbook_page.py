from __future__ import annotations

import html


def render_runbook_history_page(executions) -> str:
    rows = "".join(
        "<tr>"
        f"<td>{html.escape(item.execution_id)}</td>"
        f"<td>{html.escape(item.incident_code)}</td>"
        f"<td>{html.escape(item.operator)}</td>"
        f"<td>{html.escape(item.status)}</td>"
        f"<td>{html.escape(', '.join(item.completed_steps))}</td>"
        "</tr>"
        for item in executions
    )

    return (
        "<!doctype html><html lang='tr'><head><meta charset='utf-8'>"
        "<title>Aslan Özaslan Runbook Geçmişi</title></head><body>"
        "<h1>Runbook Yürütme Geçmişi</h1>"
        "<table><thead><tr>"
        "<th>Execution</th><th>Incident</th><th>Operatör</th>"
        "<th>Durum</th><th>Tamamlanan adımlar</th>"
        "</tr></thead><tbody>"
        f"{rows}</tbody></table>"
        "</body></html>"
    )
