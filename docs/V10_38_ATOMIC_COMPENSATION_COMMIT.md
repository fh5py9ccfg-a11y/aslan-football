# v10.38 Atomic Compensation Commit & Outbox

Handler başarıyla tamamlandığında compensation kaydı, execution kaydı, durum
indeksi ve outbox olayı tek Lua işlemiyle yazılır.

Bu yaklaşım handler tamamlandıktan sonra process çökmesi halinde kayıtların
birbirinden kopmasını engeller. Stale owner token ile atomik commit reddedilir.

Outbox olayları admin/ops endpoint'i üzerinden görüntülenebilir ve ileride mesaj
broker publisher'ı tarafından yayımlanabilir.
