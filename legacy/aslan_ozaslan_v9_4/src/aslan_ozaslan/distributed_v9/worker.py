from __future__ import annotations

from .domain import WorkerBatchReport

class OutboxWorker:
    def __init__(
        self,
        *,
        worker_id: str,
        lease_manager,
        publisher,
        state_repository,
        retry_policy,
    ):
        if not worker_id.strip():
            raise ValueError("worker_id boş olamaz")
        self.worker_id = worker_id
        self.lease_manager = lease_manager
        self.publisher = publisher
        self.state = state_repository
        self.retry_policy = retry_policy

    def run_once(self, *, limit: int = 50) -> WorkerBatchReport:
        messages = self.lease_manager.claim(
            worker_id=self.worker_id,
            limit=limit,
        )
        published = 0
        retried = 0
        dead_lettered = 0

        for message in messages:
            result = self.publisher.publish(message)
            if result.success:
                self.state.mark_published(message.message_id)
                published += 1
                continue

            next_attempt = message.attempt_count + 1
            if next_attempt >= self.retry_policy.max_attempts:
                self.state.mark_dead_letter(
                    message_id=message.message_id,
                    error=result.error or "publish_failed",
                )
                dead_lettered += 1
            else:
                self.state.mark_retry(
                    message_id=message.message_id,
                    error=result.error or "publish_failed",
                    available_at=self.retry_policy.next_available_at(
                        message.attempt_count
                    ),
                )
                retried += 1

        return WorkerBatchReport(
            worker_id=self.worker_id,
            claimed=len(messages),
            published=published,
            retried=retried,
            dead_lettered=dead_lettered,
        )
