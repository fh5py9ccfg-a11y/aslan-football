# MVP 0.1 Hızlı Başlangıç

## Başlatma

```bash
docker compose up --build
```

Tarayıcıdan:

```text
http://localhost:8000
```

## İlk kullanım

1. Kulüp oluşturun.
2. Kulübü seçin.
3. Oyuncu ve maç ekleyin.
4. Dashboard özetlerini görüntüleyin.
5. Maç sonuçlarını API üzerinden tamamlayın.

## Önemli

Bu MVP, hızlı pilot kullanım için kimlik doğrulaması olmadan açılan ayrı bir
çalışma alanıdır. Mevcut enterprise API ve güvenlik katmanları pakette korunur.
Üretim dağıtımında MVP endpoint'leri gateway policy ile sınırlandırılmalıdır.
