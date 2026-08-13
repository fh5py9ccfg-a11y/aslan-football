# API Güvenliği ve Oran Sınırlama

- API anahtarları kaynak koda yazılmaz.
- Anahtarlar yalnızca ortam değişkenlerinden okunur.
- Eksik anahtar durumunda sistem açık hata verir; sahte veri üretmez.
- Token bucket ile sağlayıcı limitleri korunur.
- Sağlayıcı limiti dolduğunda istek ertelenir veya tahmin durdurulur.
- Anahtarlar loglara, hata mesajlarına ve denetim kayıtlarına yazılmaz.
