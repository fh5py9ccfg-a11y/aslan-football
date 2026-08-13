# v11.2 Model Registry, Champion–Challenger & Calibration

## Model Registry

Model artifact URI, SHA-256 digest, feature version, training dataset ve yaşam
döngüsü durumu kayıt altına alınır.

## Champion–Challenger

Her deployment slot için champion model, challenger model ve rollout yüzdesi
saklanır. Challenger kontrollü olarak başlatılabilir, promote edilebilir veya
önceki champion'a rollback yapılabilir.

## Evaluation

Brier Score, Log Loss, Accuracy ve Calibration Error hesaplanır. Challenger
yalnızca tanımlı kalite kapılarının tamamını geçtiğinde kazanır.

## Calibration

Ham olasılıklar slope/intercept tabanlı logistic calibration ile yeniden
kalibre edilir.

## Operasyon

Model kayıt, champion, challenger, promotion, rollback ve deployment durum
endpoint'leri sağlanır.
