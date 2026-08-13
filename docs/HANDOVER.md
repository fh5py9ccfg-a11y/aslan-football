# Handover

## Teslim edilen ana bileşenler

- FastAPI backend
- Redis tabanlı veri katmanı
- Web pilot arayüzü
- Maç tahmin motoru
- Kalibrasyon ve backtest
- Pilot gözlem ve ürün analitiği
- Feature flags ve deneyler
- Backup, acceptance ve final doğrulama araçları

## İlk çalıştırma

```bash
cp .env.example .env
docker compose up --build -d
python scripts/final_pilot_setup.py
python scripts/pilot_acceptance.py
```

## Gerçek veri öncesi

```bash
python scripts/validate_import.py PLAYERS players.csv
python scripts/validate_import.py MATCHES matches.csv
```

## Kabul ölçütü

Pilot kabul sonucu `ACCEPTED`, smoke test başarılı ve gerçek veri importunda
karantinaya düşen kritik satır bulunmamalıdır.
