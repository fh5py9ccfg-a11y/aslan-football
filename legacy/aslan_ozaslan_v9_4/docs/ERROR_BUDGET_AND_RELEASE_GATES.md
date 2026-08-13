# Hata Bütçesi ve Yayın Kapıları

Sıfır hata sözü gerçekçi değildir; hedef, hatayı kullanıcıya ulaşmadan yakalamak ve
oluştuğunda güvenli şekilde durmaktır.

Canlı yayın için zorunlu kapılar:

1. Tüm otomatik testler geçmeli.
2. Veri yetersizliği senaryoları tahmin üretmemeli.
3. Sağlayıcı kesinti testi geçmeli.
4. Aynı yüzde tekrar alarmı çalışmalı.
5. Geri dönüş paketi üretilmeli.
6. Sürüm manifesti güncellenmeli.
7. Manuel kabul testi tamamlanmalı.

Kritik hata görülürse yeni tahmin üretimi durdurulur; eski tahminler de zaman damgası
ve geçersiz uyarısıyla gösterilir.
