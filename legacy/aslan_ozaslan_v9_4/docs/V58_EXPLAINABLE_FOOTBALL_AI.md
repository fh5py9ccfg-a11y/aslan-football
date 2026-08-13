# v5.8 Explainable Football AI

## Faktör katkıları
Elo, form, saha avantajı, kadro, chemistry, taktik, yorgunluk ve eksik oyuncu
gibi faktörler güven katsayılarıyla birlikte normalize edilir.

## Model fikir birliği
Ensemble üyelerinin 1X2 olasılık dağılımları karşılaştırılır. Dağılım farkı
arttıkça consensus skoru düşer.

## Güvenilirlik
Kalibrasyon hatası, örnek yeterliliği, veri tazeliği, ensemble fikir birliği ve
simülasyon kararlılığı tek güvenilirlik skorunda birleşir.

## Doğal dil
Tahmin sonucu, en güçlü pozitif ve negatif faktörlerle birlikte Türkçe açıklama
olarak üretilir.

## Üretim sınırı
Faktör katkısı nedensellik iddiası değildir. Gerçek feature attribution,
counterfactual analiz ve model-spesifik SHAP benzeri açıklamalar henüz bağlı
değildir.
