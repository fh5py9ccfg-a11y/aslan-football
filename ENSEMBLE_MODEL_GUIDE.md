# Ensemble Model Rehberi

## Eğit

```bash
python scripts/train_ensemble_model.py
```

Çıktı:

```text
TRAINED_ENSEMBLE_MODEL.json
```

## Yeni maç tahmini

```bash
python scripts/predict_with_ensemble.py \
  --home-xg 1.65 \
  --away-xg 1.10 \
  --home-elo 1580 \
  --away-elo 1510 \
  --home-form 0.70 \
  --away-form 0.45
```

## Walk-forward backtest

```bash
python scripts/ensemble_backtest.py \
  data/templates/historical_matches.csv \
  --competition "Pilot Lig" \
  --minimum-train-size 20 \
  --step-size 5
```

Model iki sinyali birleştirir:

- Poisson + xG tabanlı skor dağılımı
- Elo ve form tabanlı sonuç sinyali

Ağırlıklar ve calibration temperature, zaman sıralı validation setinde log loss
ve Brier skoru kullanılarak seçilir.
