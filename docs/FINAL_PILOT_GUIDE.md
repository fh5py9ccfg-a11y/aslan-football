# Final Pilot Guide

## En hızlı kurulum

```bash
cp .env.example .env
docker compose up --build -d
python scripts/final_pilot_setup.py
```

Bu komut:

- Demo kulübü oluşturur
- 18 oyuncu ekler
- 3 fikstür oluşturur
- Kulüp ve rakip güç profillerini hazırlar
- Aktif modeli kaydeder
- İlk maç tahmin pipeline'ını çalıştırır
- Release gate, pilot readiness ve sağlık skorunu kontrol eder

Başarılı sonuç:

```text
final_status: READY
```

## Tam doğrulama

```bash
python scripts/final_verify.py
```

Bu doğrulama smoke test, yük probe'u ve final pilot kurulumunu birlikte çalıştırır.
