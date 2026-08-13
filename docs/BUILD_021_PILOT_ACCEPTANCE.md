# Build 021 — Pilot Acceptance

## Kabul kontrolleri

- Final pilot READY
- Production güvenlik yapılandırması
- Backup ve restore doğrulaması
- Sistem sağlık skoru
- Aktif model
- Tahmin üretimi
- Pipeline çalışması
- Release gate
- Pilot readiness

## Kabul sonucu

- ACCEPTED
- CONDITIONAL
- REJECTED

Rapor SHA-256 fingerprint ile mühürlenir. Aynı kontrol içeriği aynı fingerprint'i
üretir.

## Tekrarlanabilirlik

Demo seed işlemi iki kez çalıştırılır. Oyuncu ve fikstür sayılarının değişmemesi
beklenir. Bu kontrol, kurulumun idempotent olduğunu doğrular.
