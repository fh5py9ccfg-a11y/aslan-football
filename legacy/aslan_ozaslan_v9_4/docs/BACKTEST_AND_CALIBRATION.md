# Backtest ve Kalibrasyon

Rastgele train/test bölmesi kullanılmaz. Yalnızca zaman sıralı genişleyen pencere
doğrulaması uygulanır. Hedef maç saatinden sonraki hiçbir veri özellik üretiminde
kullanılamaz.

Ölçütler:
- Accuracy: yalnızca yardımcı ölçüt
- Brier score: olasılık kalitesi
- Log-loss: aşırı emin yanlış tahmin cezası
- Kalibrasyon: modelin söylediği yüzde ile gerçekleşen oran uyumu

Yeni model; eski modele karşı zaman bazlı testte kalibrasyonu bozmadan ve belirli
liglerde çöküş göstermeden ilerlemelidir.
