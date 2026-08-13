# v10.45 Cross-Region Disaster Recovery

- Bölgesel replication checkpoint'leri
- RPO ölçümü ve promotion guard
- Topology epoch ile split-brain koruması
- Primary promotion ve failback
- RTO tahmini
- DR health görünürlüğü

Promotion yalnızca checkpoint RPO hedefi içindeyse ve beklenen topology epoch
güncelse kabul edilir.
