# Çalıştırma Rehberi

## Linux / macOS

```bash
./scripts/start.sh
```

## Windows PowerShell

```powershell
./scripts/start.ps1
```

Başlangıç akışı:

1. `.env` dosyasını hazırlar.
2. Güvensiz örnek secret değerlerini güçlü rastgele değerlerle değiştirir.
3. Docker servislerini başlatır.
4. API hazır olana kadar bekler.
5. Demo pilot verisini oluşturur.
6. Pilot kabul testini çalıştırır.

Arayüz:

```text
http://localhost:8000
```

Durdurma:

```bash
./scripts/stop.sh
```

Kod testleri:

```bash
ASLAN_SKIP_RUNTIME_CHECKS=1 python scripts/final_check.py
```

Çalışan sistemle tam doğrulama:

```bash
python scripts/final_check.py
```
