# v10.43 Event Ordering & Sequence Guarantees

Her request bir outbox partition'ıdır. Atomik Lua commit sırasında Redis INCR ile monoton sequence atanır. Publisher partition ordering state'ini ilerletir; aynı event replay'i idempotent, farklı event ile aynı sequence ve sequence boşluğu hatadır.

Outbox listeleme partition + sequence sırasına göre deterministiktir. Sayaçlar process restart sonrasında Redis'ten devam eder.
