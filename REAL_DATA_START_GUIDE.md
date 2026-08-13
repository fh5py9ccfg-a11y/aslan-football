# Gerçek Veriyle Başlangıç

## 1. Geçmiş maç şablonu

Dosya:

```text
data/templates/historical_matches.csv
```

Zorunlu alanlar:

- match_id
- competition
- season
- kickoff_at
- home_team
- away_team
- home_goals
- away_goals
- home_xg
- away_xg
- home_elo
- away_elo

## 2. Temel modeli eğit

```bash
python scripts/train_baseline_model.py
```

Çıktı:

```text
TRAINED_BASELINE_MODEL.json
```

Rapor şunları içerir:

- Lig gol ortalamaları
- Ev sahibi avantajı
- xG ağırlığı
- Elo ağırlığı
- Zaman sıralı validation doğruluğu
- Brier skoru

## 3. Gerçek veriye geçiş

Örnek dosyayı kendi geçmiş maç verinizle değiştirin:

```bash
python scripts/train_baseline_model.py gercek_maclar.csv --competition "Süper Lig"
```

En az 12 maç gereklidir. Daha güvenilir sonuç için yüzlerce veya binlerce maç
kullanılmalıdır.
