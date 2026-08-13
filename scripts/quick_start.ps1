$ErrorActionPreference = "Stop"

python scripts/quick_train.py
Write-Host ""
Write-Host "Örnek tahmin çalıştırılıyor..."

python scripts/quick_predict.py `
  --home-team "Aslan FC" `
  --away-team "Rakip FC" `
  --home-xg 1.65 `
  --away-xg 1.10 `
  --home-elo 1580 `
  --away-elo 1510 `
  --home-form 0.70 `
  --away-form 0.45
