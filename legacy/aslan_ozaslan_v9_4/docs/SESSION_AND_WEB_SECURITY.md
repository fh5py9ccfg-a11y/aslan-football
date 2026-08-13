# Oturum ve Web Güvenliği

## Oturum
- Rastgele, tahmin edilemez token
- Sunucuda yalnızca token özeti
- Süre sonu
- Açık iptal
- Rol bilgisi oturumla birlikte doğrulanır

## CSRF
Durum değiştiren tüm isteklerde oturuma bağlı CSRF token zorunludur.

## Giriş koruması
Aynı kullanıcı veya IP üzerinden tekrarlanan başarısız girişlerde geçici kilit uygulanır.

## Log güvenliği
Parola, oturum tokenı, API anahtarı ve sırlar loglara yazılmaz.

## Eksik kalan üretim adımları
- HttpOnly, Secure ve SameSite cookie
- kalıcı oturum deposu
- parola sıfırlama
- çok faktörlü doğrulama
- reverse proxy ve TLS
- gerçek kullanıcı arayüzü
