# Aslan Football — Canlı Yayına Alma

Bu paket artık Render veya Railway gibi bir bulut platformunda çalıştırılmaya
hazırdır. Canlı adres oluşturmak için bir hosting hesabına bağlanması gerekir.

## En kolay yol: Render

### 1. GitHub deposu oluştur

- GitHub hesabına giriş yap.
- Yeni, boş bir depo oluştur.
- Bu ZIP içindeki dosyaları deponun köküne yükle.
- `render.yaml` dosyasının kökte kaldığını kontrol et.

### 2. Render hesabına bağla

- Render hesabına GitHub ile giriş yap.
- **New → Blueprint** seç.
- Oluşturduğun GitHub deposunu bağla.
- Render, kökteki `render.yaml` dosyasını otomatik bulur.
- `SPORTMONKS_API_TOKEN` sorulursa şimdilik boş bırakılabilir.
- **Deploy Blueprint** düğmesine bas.

Render şunları otomatik oluşturur:

- Web uygulaması
- PostgreSQL veritabanı
- Redis/Key Value servisi
- Güvenli rastgele secret değerleri
- HTTPS adresi
- Sağlık kontrolü
- Veritabanı migration işlemleri

### 3. Telefonda aç

Dağıtım tamamlandığında buna benzer bir adres görünür:

```text
https://aslan-football-app.onrender.com
```

Bu adresi iPhone Safari'de aç.

### 4. iPhone ana ekranına ekle

1. Safari'deki **Paylaş** düğmesine bas.
2. **Ana Ekrana Ekle** seçeneğini seç.
3. **Ekle** düğmesine bas.

Artık Aslan Football telefonda uygulama gibi açılır.

## Railway alternatifi

Paketin kökünde `Dockerfile` ve `railway.json` bulunur. Railway, kökte bir
Dockerfile bulduğunda bunu kullanarak uygulamayı build edebilir. Railway'de
ayrıca PostgreSQL ve Redis servisleri eklenip şu değişkenler bağlanmalıdır:

- `DATABASE_URL`
- `REDIS_URL`
- `AUTH_TOKEN_SECRET`
- `MVP_AUTH_SECRET`
- `SESSION_MAINTENANCE_APPROVAL_SIGNING_SECRET`
- `COMPLIANCE_ATTESTATION_SECRET`

## Önemli

Bu paket canlı yayına hazırdır; fakat ben senin adına hesap açamam, ödeme
yapamam veya hosting hesabındaki **Deploy** düğmesine basamam. Canlı URL,
paket senin Render/Railway hesabına bağlandığında oluşur.
