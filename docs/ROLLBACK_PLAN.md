# Rollback Plan

## Uygulama rollback

1. Mevcut `.env` ve backup dosyasını koruyun.
2. Çalışan container'ları durdurun.
3. Önceki doğrulanmış ZIP sürümünü açın.
4. Aynı `.env` dosyasını kopyalayın.
5. `docker compose up --build -d` çalıştırın.
6. Smoke test ve pilot acceptance çalıştırın.

## Veri rollback

1. Yeni veri importunu durdurun.
2. Karantina raporunu saklayın.
3. Son doğrulanmış backup manifestini seçin.
4. Checksum ve schema doğrulamasını çalıştırın.
5. Restore işlemini kontrollü bakım penceresinde yapın.
6. Oyuncu, maç ve tahmin sayımlarını karşılaştırın.

## Model rollback

1. Aktif modeli `ARCHIVED` durumuna alın.
2. Son güvenilir modeli `ACTIVE` olarak promote edin.
3. Tahmin snapshot ve drift raporunu kontrol edin.
4. Yeni tahmin pipeline'ını tekrar çalıştırın.
