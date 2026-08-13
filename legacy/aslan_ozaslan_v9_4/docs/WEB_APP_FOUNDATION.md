# Web Uygulaması Temeli

İlk web katmanı yalnızca:
- ana durum ekranı,
- sağlık kontrolü,
- güvenli 404 yanıtı
sağlar.

Gerçek kullanıcı arayüzüne geçmeden önce:
- oturum yönetimi,
- CSRF koruması,
- güvenli cookie ayarları,
- oran sınırlama,
- giriş denemesi kilidi,
- denetim logları
tamamlanmalıdır.

Sistem gerçek veri ve doğrulanmış model olmadan kullanıcıya tahmin göstermez.
