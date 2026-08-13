# v10.14 OIDC Discovery & Claim Mapping

## Discovery
Issuer'ın `.well-known/openid-configuration` belgesi otomatik okunur ve JWKS URL,
authorization endpoint, token endpoint ve desteklenen kapsamlar önbelleğe alınır.

## Issuer allowlist
Birden fazla güvenilen issuer açık allowlist ile tanımlanabilir.

## Claim mapping
Subject ve rol claim yolları JSON yapılandırmasıyla değiştirilebilir. İç içe claim
yolları ve scope içindeki rol prefix'leri desteklenir.

## Dayanıklılık
Discovery ve JWKS ayrı TTL cache'leri kullanır. Discovery issuer uyuşmazlığı
reddedilir.

## Üretim sınırı
Discovery ilk uygulama başlangıcında senkron yapılır. Ağ kesintisinde stale-cache
fallback ve arka plan yenileme sonraki aşamada eklenmelidir.
