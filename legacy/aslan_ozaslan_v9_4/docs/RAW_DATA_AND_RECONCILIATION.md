# Ham Veri Arşivi ve Çoklu Kaynak Uzlaştırma

## Neden ham veri saklanır?

Bir tahminin neden üretildiğini sonradan açıklayabilmek için yalnızca dönüştürülmüş
özellikler değil, sağlayıcıdan gelen özgün cevap da değiştirilemez biçimde saklanır.

Her kayıt:
- sağlayıcı,
- kaynak türü,
- dış kimlik,
- çekilme zamanı,
- içerik özeti,
- özgün JSON
alanlarını taşır.

Aynı içerik tekrar gelirse çoğaltılmaz. İçerik değişirse yeni sürüm olarak eklenir.

## Kaynak çatışması

Kaynaklar farklı bilgi verirse tek kaynağa körü körüne güvenilmez.

Karar sırası:
1. Resmî kaynak
2. Sözleşmeli birincil sağlayıcı
3. İkinci güvenilir sağlayıcı
4. Düşük güvenli açık kaynak

Uzlaşma eşiği sağlanmazsa ilgili alan bilinmiyor kabul edilir ve kritik bir alansa
tahmin durdurulur.
