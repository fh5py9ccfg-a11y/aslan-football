# v10.10 Distributed Access State

WebSocket ticket ve token revocation production ortamında Redis üzerinde
saklanır. API key registry; key durumu, rol ve sürüm bilgisiyle rotate/revoke
işlemlerini destekler.

Redis API key doğrulaması şu anda SCAN kullanır. Çok büyük key setlerinde key-id
başlığıyla doğrudan lookup tercih edilmelidir.
