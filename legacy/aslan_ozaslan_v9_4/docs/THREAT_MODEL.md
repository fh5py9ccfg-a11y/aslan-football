# Tehdit ve Hata Modeli

## Veri riskleri
- Yanlış takım eşleşmesi
- Eski veya gecikmiş veri
- Aynı maçın iki kez gelmesi
- API kesintisi veya kota dolması
- Ertelenen maçın aktif görünmesi

## Model riskleri
- Aynı fallback değerinin her maça uygulanması
- Aşırı güvenli yüzdeler
- Veri sızıntısı ve geleceği görme hatası
- Kalibrasyon bozulması

## Operasyon riskleri
- API anahtarının sızması
- Hatalı sürümün canlıya alınması
- Yedeksiz veritabanı
- Geri dönüş paketinin olmaması

Her risk için otomatik kontrol, uyarı ve durdurma davranışı tanımlanacaktır.
