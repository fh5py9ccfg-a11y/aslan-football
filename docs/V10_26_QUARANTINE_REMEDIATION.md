# v10.26 Quarantine Remediation

Admin ve ops kullanıcıları karantinadaki indeksleri aktif fencing token ile
serbest bırakabilir. Release işlemi indeks anahtarı ve faz bilgisini karantina
kaydından alır, progress pending kuyruğunun başına yeniden ekler ve operator
kimliği/notuyla audit history oluşturur.

Stale lider veya aktif lease sahibi olmayan instance release yapamaz.
