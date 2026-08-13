# Kalıcı Oturum ve Fikstür Katmanı

## Kalıcı oturum
- Tokenın kendisi değil özeti saklanır.
- Süre sonu zorunludur.
- Oturum açıkça iptal edilebilir.
- Süresi dolmuş veya iptal edilmiş kayıtlar temizlenebilir.
- Canlı ortamda ayrı oturum veritabanı veya Redis tercih edilir.

## Cookie politikası
- HttpOnly
- Secure
- SameSite=Strict
- Sınırlı Max-Age
- Çıkışta açık temizleme

## Fikstür
- Upsert desteği
- Ev ve deplasman takım kimliği doğrulaması
- Zaman sıralı yaklaşan maç listesi
- Gerçek sağlayıcı bağlanmadan sahte fikstür gösterilmez
