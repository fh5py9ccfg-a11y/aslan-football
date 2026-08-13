# Üretim Veritabanı ve Yetkilendirme

## Veritabanı

İlk üretim şeması şu tabloları içerir:
- kullanıcılar,
- fikstürler,
- tahminler,
- sağlayıcı çalıştırma kayıtları,
- şema migrasyonları.

SQLite geliştirme ve tek sunucu başlangıcı için kullanılır. Gerçek ölçek büyüdüğünde
aynı şema PostgreSQL'e taşınacaktır.

## Güvenlik

- Parolalar düz metin saklanmaz.
- Scrypt tabanlı parola türetme kullanılır.
- Roller: OWNER, ADMIN, ANALYST, VIEWER.
- Model yayınlama yalnızca OWNER yetkisidir.
- Başarısız kimlik doğrulama açık kullanıcı bilgisi sızdırmaz.

## Sahiplik

Canlı veritabanı, alan adı, dağıtım hesabı ve sır yönetimi proje sahibinin hesabında
olmalıdır.
