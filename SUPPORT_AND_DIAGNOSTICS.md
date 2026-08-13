# Destek ve Tanılama

## Sistem durumunu kontrol et

Linux / macOS:

```bash
./scripts/status.sh
```

Windows PowerShell:

```powershell
./scripts/status.ps1
```

Tanılama raporu:

```bash
python scripts/diagnose.py
```

Çıktı:

```text
DIAGNOSTIC_REPORT.json
```

## Destek paketi oluştur

```bash
python scripts/create_support_bundle.py
```

Paket şunları içerir:

- Sistem tanılama raporu
- Test sonuçları
- Release manifestleri
- Secret değerleri gizlenmiş `.env` özeti

Gerçek secret değerleri destek paketine eklenmez.
