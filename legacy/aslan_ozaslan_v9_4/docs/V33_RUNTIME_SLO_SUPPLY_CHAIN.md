# v3.3 Runtime, SLO ve Supply Chain

## Container güvenliği
Production image `latest` etiketi kullanamaz ve SHA-256 digest ile sabitlenmelidir.
Bu yaklaşım aynı etiket altında farklı image yayınlanması riskini azaltır.

## Runtime politikası
Production için en az iki replica, kaynak request/limit değerleri, read-only root
filesystem ve non-root çalıştırma zorunludur.

## SLO ve hata bütçesi
Servis hedefleri ölçülebilir hedef ve zaman penceresiyle tanımlanır. Gerçekleşen
değer hedefin altındaysa SLO başarısız olur; kalan hata bütçesi ayrıca hesaplanır.

## Runbook
Bilinen incident türleri için en az iki adımlı operasyon runbook'u zorunludur.

## Supply-chain gate
CRITICAL ve HIGH güvenlik bulguları release'i engeller. MEDIUM ve LOW bulgular
warning olarak raporlanır.
