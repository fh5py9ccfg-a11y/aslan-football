# v10.8 Operational Security

## PostgreSQL audit
Audit olayları production ortamında PostgreSQL'e yazılır. Subject, resource,
outcome ve created_at alanları indekslidir.

## Audit query
Audit endpoint'i limit, offset, subject, resource ve outcome filtrelerini
destekler.

## WebSocket auth
Fixture WebSocket bağlantıları bearer token veya access_token query parametresi
ile doğrulanır ve rol kontrolünden geçer.

## Token bucket
Redis Lua token bucket burst kontrolü ve sürekli refill sağlar.

## Üretim sınırı
WebSocket token'ını query parametresinde taşımak log sızıntısı riski yaratabilir.
Tarayıcı ortamında kısa ömürlü WebSocket ticket tercih edilmelidir.
