# v5.1 Backtest, Calibration ve Lig Normalizasyonu

## Backtest
Üç yönlü maç olasılıkları için accuracy, Brier score ve log loss hesaplanır.
Yalnızca doğruluk metriğine güvenilmez.

## Calibration
Model güveni ile gerçekleşen sonuç oranı bin bazında karşılaştırılır.
Expected Calibration Error raporlanır.

## Ligler arası normalizasyon
Takım rating'i lig ortalaması ve ölçeğine göre standartlaştırılır. Böylece farklı
liglerdeki nominal Elo değerleri doğrudan karşılaştırılmak yerine normalize edilir.

## Futbol model registry
Model sürümleri lig bazında kaydedilir ve aynı model/lig için yalnızca bir sürüm
aktif tutulur.

## Üretim sınırı
Bu araçlar doğrulama altyapısıdır. Güvenilir sonuç için zaman sıralı gerçek veri,
veri sızıntısı kontrolleri ve yeterli örnek hacmi gerekir.
