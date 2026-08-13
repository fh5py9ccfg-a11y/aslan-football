# Gol Modeli ve Takım Güç Derecelendirmesi

## Elo

Elo puanı takımın uzun dönem gücünü izler. Ev sahibi avantajı ayrı parametredir.
Bir maç sonucu geldikten sonra iki takımın puanı birlikte güncellenir.

## Beklenen gol

Beklenen gol tahmini şu bileşenlerden beslenir:
- hücum gücü,
- rakip savunma gücü,
- son form puanı,
- Elo farkı,
- lig gol ortalaması,
- iç saha avantajı.

Bu temel model ileride xG sağlayıcıları ve kadro etkisiyle genişletilecektir.

## Poisson skor modeli

Ev ve deplasman beklenen golleri, skor dağılımına çevrilir. Model:
- 1-X-2 olasılıklarını,
- en olası skorları,
- toplam gol dağılımını
üretebilir.

Kesilmiş skor aralığı sonrasında olasılık kütlesi yeniden normalize edilir.
