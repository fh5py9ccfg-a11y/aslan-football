# Build 019 — Feature Flags & Controlled Experiments

## Feature flags

- Açık/kapalı durumu
- Rollout yüzdesi
- Rol bazlı erişim
- Deterministik kullanıcı bucket'ı
- Varyant seçimi

## A/B deneyleri

Durumlar:

- DRAFT
- RUNNING
- PAUSED
- COMPLETED
- ROLLED_BACK

## Deney ölçümü

- Kontrol ve treatment ortalaması
- Başarı oranı
- Uplift yüzdesi
- Kazanan varyant
- Yayını genişletme veya geri alma önerisi

## Güvenli rollback

Deney tek işlemle ROLLED_BACK durumuna alınabilir. Bağlı feature flag kapatılıp
rollout yüzdesi sıfırlanabilir.
