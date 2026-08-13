# v10.9 Access Gateway

- 30 saniyelik tek kullanımlık WebSocket ticket
- Bearer token JTI ve revocation
- Provider X-API-Key kimlik doğrulaması
- Ayrı provider event endpoint'i

Test ortamında ticket ve revocation bellek içindedir. Çoklu instance üretimde
Redis repository kullanılmalıdır.
