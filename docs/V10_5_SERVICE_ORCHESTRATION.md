# v10.5 Service Orchestration

## Database migrations
Alembic ilk migration; match event, outbox ve message receipt tablolarını kurar.

## Runtime services
- API
- PostgreSQL outbox worker
- Redis event consumer bridge
- Opsiyonel Sportmonks live sync scheduler
- PostgreSQL
- Redis

## Health and startup ordering
Docker Compose healthcheck ve `depends_on.condition` ile servis başlangıç sırası
yönetilir.

## Integration profile
Container entegrasyon testi opt-in olarak ayrı compose dosyasında tanımlanır.
Bu çalışma ortamında Docker daemon çalıştırılmamıştır.
