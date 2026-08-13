# Kurtarma ve Bakım Planı

## Hata bulunduğunda

1. Ekran görüntüsü ve maç kimliği kaydedilir.
2. Hata otomatik test olarak yazılır.
3. Düzeltme ayrı sürümde yapılır.
4. Tüm testler çalıştırılır.
5. Test ortamında aynı maç yeniden denenir.
6. Canlıya alınır.
7. Önceki sürüme dönüş paketi saklanır.

## Yedekleme

- Kaynak kod: Git deposu.
- Ortam değişkenleri: şifreli yedek.
- Veritabanı: günlük otomatik yedek.
- Model çıktıları: denetim kaydı.
- Her canlı yayın: etiketli sürüm.

## Sahiplik

Proje sahibi kaynak kod, yayın hesabı, alan adı ve API anahtarlarının sahibi olmalıdır.
Hiçbir kritik parça yalnızca sohbet geçmişinde tutulmaz.
