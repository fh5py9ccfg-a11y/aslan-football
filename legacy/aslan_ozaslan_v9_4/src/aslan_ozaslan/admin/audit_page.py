from __future__ import annotations

import html


def render_audit_page(records) -> str:
    rows = "".join(
        "<tr>"
        f"<td>{html.escape(record.created_at)}</td>"
        f"<td>{html.escape(record.actor_id)}</td>"
        f"<td>{html.escape(record.action)}</td>"
        f"<td>{html.escape(record.resource_type)}</td>"
        f"<td>{html.escape(record.resource_id)}</td>"
        "</tr>"
        for record in records
    )

    return (
        "<!doctype html><html lang='tr'><head><meta charset='utf-8'>"
        "<title>Aslan Özaslan Audit</title></head><body>"
        "<h1>Denetim Kayıtları</h1>"
        "<table><thead><tr>"
        "<th>Zaman</th><th>Aktör</th><th>İşlem</th>"
        "<th>Kaynak türü</th><th>Kaynak</th>"
        "</tr></thead><tbody>"
        f"{rows}</tbody></table>"
        "</body></html>"
    )
