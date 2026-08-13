# v2.5 Sonuç, Drift ve Operasyon Katmanı

## Kalıcı sonuçlar
Maç sonuçları ve sonuçlandırılmış tahminler ayrı tablolarda saklanır. Bu ayrım,
sağlayıcıdan gelen ham sonuç ile model değerlendirmesini birbirinden ayırır.

## Çok ölçütlü drift
Drift artık yalnızca isabet oranına bakmaz:
- accuracy,
- log-loss,
- Brier score
ayrı karşılaştırılır.

Minimum örnek sayısı dolmadan drift kararı verilmez.

## Sonuç sağlayıcı adaptörü
Gerçek API bağımlılığı çekirdek iş mantığından ayrıdır. Adaptör yalnızca tamamlanan
ve kimliği eşleşen maçları kalıcı depoya aktarır.

## Yönetim görünümü
İlk yönetim özeti:
- sağlayıcı sağlığı,
- şampiyon model,
- bekleyen fikstür,
- sonuçlandırılmamış tahmin,
- drift alarmı,
- yayın hazırlığı
bilgilerini tek yerde toplar.
