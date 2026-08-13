# Aslan Football — Buradan Başla

## 1. Sistemi başlat

```bash
cp .env.example .env
```

`.env` içindeki secret değerlerini değiştirin.

```bash
./scripts/start.sh
```

Arayüz:

```text
http://localhost:8000
```

## 2. Gerçek veriyi doğrula

Hazır şablonlar:

- `data/templates/players.csv`
- `data/templates/matches.csv`

Doğrulama:

```bash
python scripts/validate_import.py PLAYERS data/templates/players.csv
python scripts/validate_import.py MATCHES data/templates/matches.csv
```

## 3. Final kontrol

Sadece kod ve test kontrolü:

```bash
ASLAN_SKIP_RUNTIME_CHECKS=1 python scripts/final_check.py
```

Çalışan sistemle tam kontrol:

```bash
python scripts/final_check.py
```

## 4. Kullanılan ana akış

1. Oyuncuları ve fikstürleri yükle.
2. Kulüp ve rakip profillerini oluştur.
3. Tahmin pipeline'ını çalıştır.
4. Veri kalite ve güven uyarılarını incele.
5. Maç karar raporunu üret.
6. Gerçek sonuç geldiğinde maç sonrası öğrenmeyi çalıştır.

Bu paket karar desteğidir; kesin maç sonucu garantisi vermez.


En kolay başlangıç: `./scripts/start.sh`. Windows için `./scripts/start.ps1`.
