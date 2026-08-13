# v5.2 Zaman Sıralı Doğrulama ve Model Promotion

## Expanding window
Train seti zaman içinde büyür, validation seti daima gelecekte kalır. Böylece
gelecek verinin eğitim sürecine sızması önlenir.

## Leakage guard
Her feature'ın kullanılabilir olduğu zaman, tahmin zamanı ile karşılaştırılır.
Tahmin anından sonra oluşan feature model promotion'ı doğrudan engeller.

## Baseline karşılaştırması
Candidate model aynı örnek setindeki baseline ile Brier score, log loss ve
accuracy bakımından karşılaştırılır.

## Promotion gate
Bir model ancak:
- yeterli örnek sayısına,
- gerekli Brier iyileşmesine,
- kabul edilebilir calibration error'a,
- veri sızıntısı bulunmamasına,
- baseline'dan daha iyi olmasına
sahipse aktif sürüm olmaya aday kabul edilir.

## Üretim sınırı
Promotion kararı modelin otomatik olarak production'a alınması değildir.
Release approval ve mevcut production kontrol merkezi ayrıca çalışmalıdır.
