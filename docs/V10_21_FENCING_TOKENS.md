# v10.21 Fencing Tokens

Her başarılı lease acquisition monoton artan Redis epoch üretir. Bakım
mutasyonları bu token ile Lua üzerinden korunur. Yeni lider daha yüksek epoch
yazdıktan sonra eski liderin SREM, EXPIRE ve DELETE işlemleri reddedilir.

Bu koruma heartbeat gecikmesi ve ağ bölünmesi sırasında split-brain bakım
yazmalarını önler.
