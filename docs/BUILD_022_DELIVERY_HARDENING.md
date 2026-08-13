# Build 022 — Delivery Hardening

## CSV karantina akışı

Gerçek pilot verileri sisteme alınmadan önce doğrulanır.

Oyuncu CSV kontrolleri:

- Zorunlu alanlar
- Pozisyon kodu
- Yaş aralığı
- Negatif piyasa değeri

Maç CSV kontrolleri:

- Zorunlu alanlar
- Saha türü
- Unix kickoff zamanı

Hatalı satırlar tamamen reddedilmek yerine karantina dosyasına ayrılır.

```bash
python scripts/validate_import.py PLAYERS players.csv
python scripts/validate_import.py MATCHES matches.csv
```

## Teslim manifesti

```bash
python scripts/create_delivery_manifest.py
```

Manifest; dosya sayısı, test sonucu, dokümanlar, operasyon scriptleri ve paket
checksum bilgisini içerir.
