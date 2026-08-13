# v10.35 Compensation Orchestration

## Otomatik worker
PENDING ve zamanı gelmiş RETRY_SCHEDULED kayıtları arka plan worker'ı tarafından
işlenir.

## Retry ve backoff
Geçici hatalarda exponential backoff uygulanır. Her hata attempt sayısını artırır.

## Dead-letter
Maksimum deneme sayısı aşıldığında kayıt DEAD_LETTER durumuna taşınır ve otomatik
işleme durur.

## Manuel requeue
Admin dead-letter veya başarısız kaydı yeniden PENDING durumuna alabilir.

## Handler registry
Her compensation action ayrı idempotent handler ile eşleştirilir.

## Üretim sınırı
Varsayılan reconcile handler no-op'tur. Gerçek dış sistem adaptörü bağlanmadan
telafi tamamlanmış sayılmamalıdır; production kurulumunda handler override
edilmelidir.
