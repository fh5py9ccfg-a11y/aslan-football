# v10.7 Distributed Guards & Audit

Redis fixed-window rate limiting, audit kayıtları, request body sınırı ve
graceful shutdown/readiness desteği eklenmiştir.

Test ortamı bellek içi limiter ve audit repository kullanır. Üretim ortamı
Redis limiter ve JSON audit deposu kullanır.
