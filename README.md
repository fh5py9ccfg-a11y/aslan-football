# Aslan Football — Final Pilot

Futbol maç analizi ve olasılık tahmin sistemi.

## Hızlı başlatma

```bash
./scripts/start.sh
```

Arayüz:

```text
http://localhost:8000
```

## Gerçek veri şablonları

- `data/templates/players.csv`
- `data/templates/matches.csv`

## Final doğrulama

```bash
ASLAN_SKIP_RUNTIME_CHECKS=1 python scripts/final_check.py
```

Çalışan Docker ortamıyla:

```bash
python scripts/final_check.py
```

Ayrıntılı kullanım için `FINAL_START_HERE.md` dosyasını okuyun.

Windows PowerShell: `./scripts/start.ps1`


## Sorun giderme

```bash
python scripts/diagnose.py
python scripts/create_support_bundle.py
```

Ayrıntılar: `SUPPORT_AND_DIAGNOSTICS.md`


## Gerçek geçmiş maç verisi

```bash
python scripts/train_baseline_model.py
```

Ayrıntılar: `REAL_DATA_START_GUIDE.md`


## Ensemble model

```bash
python scripts/train_ensemble_model.py
python scripts/ensemble_backtest.py
```

Ayrıntılar: `ENSEMBLE_MODEL_GUIDE.md`


## Takım bazlı rolling model

```bash
python scripts/train_rolling_model.py gercek_maclar.csv --competition "Süper Lig"
```

Ayrıntılar: `ROLLING_MODEL_GUIDE.md`


## En hızlı kullanım

```bash
python scripts/quick_train.py
python scripts/quick_predict.py \
  --home-xg 1.65 \
  --away-xg 1.10 \
  --home-elo 1580 \
  --away-elo 1510
```

Ayrıntılar: `QUICK_USE.md`
