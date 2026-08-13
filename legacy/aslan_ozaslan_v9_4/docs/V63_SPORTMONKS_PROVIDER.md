# v6.3 Sportmonks Provider Connection

## Doğrulanan resmî davranışlar
- API token başlıkta gönderilebilir.
- Canlı maçlar için in-play livescore ucu kullanılır.
- Son güncellenen livescore ucu, kısa aralıkta değişen maçları verir.
- Fikstür sonuçları sayfalanabilir ve `has_more` izlenir.
- `per_page` üst sınırı 50'dir.

## Güvenlik
`SPORTMONKS_API_TOKEN` yoksa hiçbir dış istek gönderilmez. Anahtar URL'ye,
arayüze veya loga eklenmez.

## Canlı veri
Provider yanıtı ortak canlı fikstür nesnesine dönüştürülür. Eksik skor, dakika,
durum veya takım alanları tahmin edilmez.

## Üretim sınırı
Bu pakette gerçek API anahtarı bulunmaz. Bu nedenle canlı Sportmonks isteği
çalıştırıldığı iddia edilmez; bağlantı kodu sahte transport testleriyle
doğrulanmıştır.
