# v11.3 Model Monitoring & Drift Intelligence

## Live model health

Ground truth geldikçe accuracy, Brier Score, Log Loss, mean confidence ve
birleşik model health score güncellenir.

## Prediction drift

Baseline ve current prediction dağılımları PSI ile karşılaştırılır.

## Feature drift

Feature ortalama kayması baseline standart sapmasına göre ölçülür.

## Severity ve review queue

Drift sinyalleri LOW, MEDIUM, HIGH veya CRITICAL olarak sınıflandırılır. HIGH
ve CRITICAL sinyaller otomatik olarak açık inceleme kaydı oluşturur.

## Shadow evaluation

Champion ve shadow model çıktıları mean absolute difference ve maksimum fark
ile karşılaştırılır.
