# Build 017 — Pilot Observability

## Telemetri

Kategoriler:

- API
- PREDICTION
- PIPELINE
- INTEGRATION
- SECURITY
- BACKUP

Seviyeler:

- INFO
- WARNING
- ERROR
- CRITICAL

## Incident yönetimi

Durumlar:

- OPEN
- INVESTIGATING
- MITIGATED
- RESOLVED

## Sağlık skoru

Skor şu sinyallerden hesaplanır:

- Hata sayısı
- Uyarı sayısı
- p95 yanıt süresi
- Açık incident sayısı

Sonuç:

- HEALTHY
- DEGRADED
- UNHEALTHY

## Alarm kuralları

- Kritik sağlık skoru
- p95 > 500 ms
- En az 3 açık incident
- Bozulma uyarıları
