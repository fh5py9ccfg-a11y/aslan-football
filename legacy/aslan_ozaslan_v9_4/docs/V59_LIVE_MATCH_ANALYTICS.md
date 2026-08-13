# v5.9 Canlı Maç Analitiği

Gol, şut, isabetli şut, kart, tehlikeli atak ve oyuncu değişikliği olayları
kimlikleriyle saklanır; aynı event ikinci kez işlenmez. Son zaman penceresindeki
olaylardan momentum hesaplanır. Skor, dakika, kırmızı kart ve momentum bilgisiyle
1X2 olasılıkları güncellenir.

Bu sürüm gerçek streaming altyapısı değildir. Kafka/NATS, geç gelen olaylar,
event correction ve kalıcı checkpoint henüz bağlı değildir.
