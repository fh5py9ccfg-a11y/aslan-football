# Arama Motoru Mimarisi

## Çözülen sorunlar

- Türkçe karakter ve büyük/küçük harf tutarsızlığı
- Aynı sorgunun farklı yazımlarında sonuç kaçırma
- Düşük güvenli kaynakların üst sıralara çıkması
- Eski haberlerin yeni verinin önüne geçmesi
- Takım ve lig bağlamının kaybolması
- Arama önbelleğinin güncel indeksle uyuşmaması
- İlgisiz belgelerin sonuçlara karışması

## Sıralama sinyalleri

1. Başlık eşleşmesi
2. Gövde eşleşmesi
3. Kaynak güven puanı
4. Yayın güncelliği
5. Takım kimliği eşleşmesi
6. Organizasyon kimliği eşleşmesi

## Değişmez kurallar

- Arama sonucu doğrudan model girdisi değildir.
- Resmî kaynak, forum veya tahmin sitesiyle aynı güven düzeyinde değerlendirilemez.
- Kaynağı, tarihi veya takım kimliği belirsiz belge kritik veri olarak kullanılamaz.
- İndeks değişince önbellek otomatik geçersiz olur.
- Boş veya anlamsız sorgu sonuç üretmez.
