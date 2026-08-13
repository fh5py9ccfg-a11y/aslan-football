# v10.12 Identity Tokens

Standart üç parçalı JWT access token; kid, issuer, audience, nbf, exp, jti ve
token_use alanlarını kullanır. Signing-key rotation sırasında eski key ring'de
kaldığı sürece mevcut access tokenlar doğrulanır.

Opaque refresh tokenlar tek kullanımlıdır. Her refresh yeni secret üretir ve
eski token replay girişimi reddedilir.

Bu sürüm HS256 kullanır. Kurumsal OIDC için RS256/ES256 ve JWKS sonraki adımdır.
