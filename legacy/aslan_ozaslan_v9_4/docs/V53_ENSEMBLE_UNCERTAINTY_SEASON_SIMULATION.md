# v5.3 Ensemble, Belirsizlik ve Sezon Simülasyonu

## Ensemble
Birden fazla modelin 1X2 olasılıkları ağırlıklı ortalama ile birleştirilir.
Ağırlıklar validation Brier score ve log loss değerlerinden türetilebilir.

## Belirsizlik
Tahmin dağılımının entropisi hesaplanır. Sonuç yalnızca favoriyi değil,
tahminin ne kadar kararsız olduğunu da gösterir.

## Monte Carlo sezon simülasyonu
Kalan fikstür binlerce kez simüle edilir. Takım bazında:
- ortalama puan,
- şampiyonluk olasılığı,
- ilk dört olasılığı,
- küme düşme olasılığı
üretilir.

## Üretim sınırı
Simülasyon kalitesi doğrudan maç olasılıklarının kalitesine bağlıdır.
Kalibre edilmemiş veya veri sızıntılı model çıktıları sezon projeksiyonuna
girdi olarak kabul edilmemelidir.
