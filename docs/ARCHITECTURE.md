# Aslan Özaslan v10 MVP Architecture

## Monorepo
- `apps/api`: FastAPI REST + WebSocket uygulaması
- `apps/worker`: arka plan worker başlangıç noktası
- `packages/football_core`: framework bağımsız domain çekirdeği
- `infra`: PostgreSQL ve container yapılandırmaları
- `legacy`: doğrulanmış v9.4 kod tabanı

## Çalışan MVP akışı
1. Fixture event REST endpoint'e gönderilir.
2. Domain olayı doğrulanır.
3. Repository idempotency kontrolü yapar.
4. Maç durumu eventlerden yeniden oluşturulur.
5. Yeni durum WebSocket abonelerine yayınlanır.

## Sonraki gerçek entegrasyon
In-memory repository PostgreSQL event store ile değiştirilecek. Legacy v9.4
ingestion/outbox bileşenleri worker içine taşınacak ve Sportmonks API istemcisine
bağlanacak.
