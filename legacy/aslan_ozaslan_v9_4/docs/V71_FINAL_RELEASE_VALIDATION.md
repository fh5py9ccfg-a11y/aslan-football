# v7.1 Final Release Validation

## Secret inspection
API anahtarları yalnızca ortam değişkeni veya harici secret manager üzerinden
sağlanır. Paket içine secret yazılmaz.

## Smoke test
Provider yapılandırması, gerçek fixture fetch, event store ve decision engine
kontrol edilir.

## Production readiness
HTTPS, güvenli secret saklama, yedekleme, monitoring, alerting, provider token
ve rollback hazırlığı denetlenir.

## Final gate
Final v7 yalnızca:
- minimum test sayısı,
- başarılı smoke test,
- gerçek provider doğrulaması,
- production environment readiness,
- platform readiness
sağlandığında onaylanır.

## Mevcut durum
Bu paket final doğrulama altyapısını hazırlar. Gerçek token ve canlı fixture
olmadan v7.0-final ilan edilmez.
