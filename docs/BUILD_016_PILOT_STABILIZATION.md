# Build 016 — Pilot Stabilization

## Güvenlik denetimi

- Production ortamı kontrolü
- Güçlü auth secret kontrolü
- Varsayılan demo secret engeli
- Oturum TTL kontrolü
- Redis prefix doğrulaması

## Yedekleme

Kulüp bazında şu bölümler alınır:

- Kulüp
- Oyuncular
- Maçlar
- Rakipler
- Tahminler
- Model registry

Backup SHA-256 checksum ile korunur. Restore işleminden önce schema, zorunlu
bölümler ve checksum doğrulanır.

## Operasyon araçları

```bash
python scripts/smoke_test.py
python scripts/load_probe.py
python scripts/create_backup.py
```

## API sözleşmesi

Mevcut route listesi normalize edilip checksum ile snapshot olarak
kaydedilebilir. Beklenmeyen API değişiklikleri sürümler arasında izlenebilir.
