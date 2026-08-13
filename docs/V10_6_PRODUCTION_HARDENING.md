# v10.6 Production Hardening

## Authentication
HMAC-SHA256 imzalı, süreli bearer token uygulanır.

## Authorization
Fixture write, read ve metrics endpoint'leri rol tabanlı korunur.

## Rate limiting
İstemci IP ve endpoint bazlı sliding-window limiter uygulanır.

## Security headers
CSP, frame deny, nosniff, referrer ve permissions policy başlıkları eklenir.

## Resilience
Sportmonks istemcisi circuit breaker ile korunur.

## Üretim sınırı
Token yapısı standart JWT değildir ve merkezi identity provider yerine yerel
HMAC kullanır. Çoklu instance rate limiting için Redis tabanlı limiter gerekir.
