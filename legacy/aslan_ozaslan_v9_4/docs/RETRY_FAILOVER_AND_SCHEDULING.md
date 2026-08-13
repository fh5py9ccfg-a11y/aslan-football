# Yeniden Deneme, Sağlayıcı Geçişi ve İş Zamanlama

## Yeniden deneme

Yalnızca geçici ağ ve zaman aşımı hataları yeniden denenir. Kodlama, şema veya
kimlik doğrulama hataları tekrar edilmez; doğrudan görünür hata oluşturur.
Gecikme katlanarak artar ve üst sınırı vardır.

## Sağlayıcı geçişi

Sağlayıcılar açık öncelik sırasına sahiptir. Birincil sağlayıcı güvenilir veri
veremezse ikincil sağlayıcı denenir. Hiçbiri veri vermezse tahmin üretilmez.

## Yinelenen iş engeli

Aynı maç ve veri sürümü için iki eşzamanlı analiz çalıştırılmaz. Her işin
`deduplication_key` değeri bulunur. Başarısız iş sahte başarı sonucu oluşturmaz.

## Sabit dağılım alarmı

Üç farklı maçta aynı tam 1-X-2 dağılımı görülürse bu bir sistem olayı kabul edilir.
Tahmin akışı durdurulur ve veri/model incelemesi yapılır.
