# Oran Piyasası Verisi Politikası

Bahis oranı modelin gerçeği değildir; ayrı bir piyasa sinyalidir.

- Oranlar marjdan arındırılarak normalize edilir.
- İlk oran ve güncel oran ayrı saklanır.
- Ani hareketler alarm üretir ancak otomatik tahmin yönü belirlemez.
- Tek bookmaker verisi yeterli kabul edilmez.
- Kapanış oranı yalnızca önceden belirlenmiş kesim saatine kadar kullanılabilir.
- Gelecek bilgisi sızıntısını önlemek için maç başladıktan sonraki oran verisi backtestte yasaktır.
