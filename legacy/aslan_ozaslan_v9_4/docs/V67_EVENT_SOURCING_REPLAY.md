# v6.7 Event Sourcing & Replay

Append-only SQLite event store, deterministik maç state projector'ı, periyodik
snapshot, sequence bazlı time-travel replay, replay verification ve crash
recovery eklendi.

Bu sürüm yerel tek-writer temelidir. Dağıtık event store, optimistic concurrency
ve çoklu writer koordinasyonu henüz bağlı değildir.
