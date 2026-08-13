# v10.18 Session Index Maintenance

## Orphan temizliği
Session kaydı TTL ile silinmiş ancak subject veya family setinde kalmış session
ID'leri periyodik olarak temizlenir.

## TTL senkronizasyonu
İndeks setlerinin TTL değeri, ilgili canlı session kayıtlarının en uzun kalan
TTL süresiyle uyumlu hale getirilir.

## Bakım worker'ı
Production ortamında arka planda çalışan bakım görevi belirli aralıklarla subject
ve family indekslerini tarar.

## Operasyonel görünürlük
Admin ve ops kullanıcıları son bakım raporunu görebilir ve bakım turunu manuel
tetikleyebilir.

## Üretim sınırı
Bakım worker'ı indeks anahtarlarını SCAN ile bulur. Bu yol kimlik doğrulama
isteklerinin kritik yolunda değildir ve yalnızca arka plan bakımı için kullanılır.
