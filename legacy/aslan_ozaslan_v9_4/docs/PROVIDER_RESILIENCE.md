# Sağlayıcı Dayanıklılığı

## Circuit breaker

Bir sağlayıcı art arda hata verirse sistem:
- çağrıları geçici olarak durdurur,
- sağlayıcıyı sağlıksız işaretler,
- eski veya varsayılan veriyle tahmin üretmez,
- iyileşme süresinden sonra kontrollü deneme yapar.

## Yasak davranış

Sağlayıcı çöktüğünde sabit yüzde, sahte kadro, geçmiş maçtan kalma cache veya
başka maçın verisiyle sonuç üretmek kesinlikle yasaktır.
