# v10.13 OIDC & JWKS Federation

## Harici OIDC
API, yerel JWT tokenlarını doğruladıktan sonra yapılandırılmışsa harici OIDC
issuer tokenlarını RS256 ile doğrular.

## JWKS cache
RSA public key'ler `kid` bazında önbelleğe alınır. TTL dolduğunda veya bilinmeyen
kid geldiğinde JWKS yeniden yüklenir.

## Claim doğrulaması
Issuer, audience, nbf, exp, subject ve RS256 imza doğrulanır. Roller `roles`,
`realm_access.roles` veya `role:` scope'larından çıkarılabilir.

## Üretim sınırı
OIDC discovery dokümanı henüz otomatik okunmaz; issuer, audience ve JWKS URL
ortam değişkenleriyle açıkça yapılandırılır.
