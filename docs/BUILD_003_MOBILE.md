# Build 003 — Flutter Mobile Companion

## Teslim edilenler

- Flutter proje yapısı
- Mobil login
- Token saklama
- Kulüp seçimi ve demo veri kurulumu
- Dashboard kartları
- Oyuncu listesi
- Maç listesi
- Drawer ve bottom navigation
- Backend mobile capability endpoint'i

## Çalıştırma

```bash
docker compose up --build
```

```bash
cd apps/mobile
flutter pub get
flutter run --dart-define=ASLAN_API_URL=http://10.0.2.2:8000
```

Flutter SDK bu paket içinde yer almaz.
