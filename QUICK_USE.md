# Aslan Football — Hızlı Kullanım

## 1. Modeli hazırla

```bash
python scripts/quick_train.py
```

## 2. Tahmin üret

```bash
python scripts/quick_predict.py \
  --home-team "Galatasaray" \
  --away-team "Rakip" \
  --home-xg 1.75 \
  --away-xg 1.05 \
  --home-elo 1600 \
  --away-elo 1510 \
  --home-form 0.72 \
  --away-form 0.44
```

## Tek komut demo

Linux / macOS:

```bash
./scripts/quick_start.sh
```

Windows PowerShell:

```powershell
./scripts/quick_start.ps1
```

## Girdi açıklaması

- `home-xg`: Ev takımının beklenen gol değeri
- `away-xg`: Deplasman takımının beklenen gol değeri
- `home-elo`: Ev takımının Elo puanı
- `away-elo`: Deplasman takımının Elo puanı
- `home-form`: 0–1 arasında son dönem formu
- `away-form`: 0–1 arasında son dönem formu

Çıktı:

- Ev kazanır olasılığı
- Beraberlik olasılığı
- Deplasman kazanır olasılığı
- Tahmini skor
- Önerilen sonuç
