# v7.0 Release Candidate

## Birleşik üretim akışı
Provider eventleri reconciliation katmanından geçer, event store'a yazılır,
canlı karar motoru yeniden çalıştırılır ve karar kalite penceresine eklenir.

## Readiness
Provider, event store, decision engine ve monitoring birlikte hazır değilse
production akışı başlatılmaz. Safe mode aktifse sistem release'i engeller.

## Release gate
Tam test paketi, minimum test sayısı ve platform readiness zorunludur.
Gerçek Sportmonks canlı API doğrulaması eksikse bu durum blocker değil, açık
uyarı olarak raporlanır.

## Sürüm durumu
Bu sürüm v7.0-rc1'dir. Kod birleşik akış ve release readiness bakımından test
edilmiştir; gerçek API anahtarıyla kontrollü smoke test yapılmadan final v7.0
olarak işaretlenmez.
