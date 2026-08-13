# v5.0 Futbol Zekâsı Temeli

Çoklu lig alan modeli, takım form analizi, yeni nesil Elo rating katmanı ve
açıklanabilir matchup motoru eklendi.

Bu katman mevcut `models.py`, eski Elo sistemi ve lig analitiğini değiştirmez;
geriye dönük uyumluluk için ayrı `football` ve `ratings_v5` namespace'lerinde
çalışır.

Canlı veri adaptörü, ligler arası normalizasyon ve katsayı kalibrasyonu henüz
tamamlanmamıştır. Bu değerler backtest ile doğrulanmadan üretim gerçeği olarak
kabul edilmemelidir.
