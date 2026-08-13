# Rolling Team Model

Bu model yalnızca maçtan önce mevcut olan takım geçmişini kullanır.

Özellikler:

1. Ev xG
2. Deplasman xG
3. Elo farkı
4. Ev takımının son 5 puan oranı
5. Deplasman takımının son 5 puan oranı
6. Ev takımının son 5 gol farkı
7. Deplasman takımının son 5 gol farkı
8. Ev takımının son 5 xG farkı
9. Deplasman takımının son 5 xG farkı
10. Ev takımının geçmiş maç sayısı
11. Deplasman takımının geçmiş maç sayısı

## Eğitim

```bash
python scripts/train_rolling_model.py \
  gercek_maclar.csv \
  --competition "Süper Lig"
```

## Tahmin

```bash
python scripts/predict_with_rolling_model.py \
  --features "1.7,1.0,0.20,0.70,0.40,0.50,-0.20,0.35,-0.10,12,12"
```

Model çok sınıflı lojistik regresyondur. Özellikler yalnızca geçmiş maçlardan
üretilir; hedef maçın sonucu veya gelecekteki maçlar kullanılmaz.
