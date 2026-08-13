# v12.4 Deployment Verification & Rollback Orchestrator

## Verification sessions

Her progressive-delivery plan için deployment slot'una bağlı doğrulama oturumu
oluşturulur. Gerekli minimum check sayısı planlanabilir.

## Evidence checks

Health, smoke, metric ve benzeri doğrulama kanıtları pass/fail sonucu, eşik,
ölçüm değeri ve açıklamayla saklanır.

## Finalization

Zorunlu check'ler başarıyla tamamlanmadan ve rollout COMPLETED durumuna gelmeden
deployment doğrulanmış kabul edilmez.

## Rollback execution

Bir check başarısız olduğunda veya progressive-delivery katmanı rollback kararı
verdiğinde model deployment manager üzerinden önceki champion geri yüklenir.

## Idempotency

Aynı verification session için rollback yalnızca bir kez uygulanır; sonraki
çağrılar mevcut sonucu döndürür.
