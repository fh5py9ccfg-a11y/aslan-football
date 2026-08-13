# Aslan Football Mobile

Flutter tabanlı mobil teknik ekip istemcisi.

## Çalıştırma

Backend'i başlatın:

```bash
docker compose up --build
```

Flutter uygulaması:

```bash
cd apps/mobile
flutter pub get
flutter run --dart-define=ASLAN_API_URL=http://10.0.2.2:8000
```

Android emülatörü için `10.0.2.2`, fiziksel cihaz için bilgisayarınızın yerel
IP adresi kullanılmalıdır.

## İlk ekranlar

- Giriş
- Dashboard
- Oyuncular
- Maçlar
- Responsive drawer ve bottom navigation
