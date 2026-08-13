def render_broker_operations_page(c,r):
 return f"<h1>Broker Operations</h1><p>Inbox: {c['inbox']}</p><p>Tamamlanan: {c['completed']}</p><p>Dead letter: {c['dead_letter']}</p><p>Outbox: {c['pending_outbox']}</p><p>Processed: {r.processed}</p>"
