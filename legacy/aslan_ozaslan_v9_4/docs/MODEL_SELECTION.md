# Model Karşılaştırma ve Şampiyon Model

Model seçimi yalnızca isabet oranına göre yapılmaz.

Öncelik sırası:
1. Log-loss
2. Brier score
3. Kalibrasyon hatası
4. Accuracy

Yeni model canlıya alınmadan önce mevcut şampiyon modele karşı aynı zaman bazlı
backtest pencerelerinde değerlendirilir. Bir ligde belirgin çöküş varsa genel
ortalama iyi görünse bile model reddedilir.
