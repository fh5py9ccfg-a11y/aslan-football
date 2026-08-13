from __future__ import annotations
import asyncio
from dataclasses import dataclass

from .quorum_execution import ExecutionOwnershipLost
from .quorum_execution_heartbeat import QuorumExecutionHeartbeat

@dataclass(frozen=True)
class GuardedExecutionResult:
    result: object | None
    ownership_lost: bool
    error: str | None

class QuorumExecutionGuard:
    def __init__(
        self,
        *,
        repository,
        heartbeat_interval_seconds: float,
    ):
        if heartbeat_interval_seconds <= 0:
            raise ValueError(
                "heartbeat_interval_seconds pozitif olmalıdır"
            )
        self.repository = repository
        self.heartbeat_interval_seconds = (
            heartbeat_interval_seconds
        )

    async def run(
        self,
        *,
        record,
        operation,
    ) -> GuardedExecutionResult:
        heartbeat = QuorumExecutionHeartbeat(
            repository=self.repository,
            record=record,
            interval_seconds=(
                self.heartbeat_interval_seconds
            ),
        )
        await heartbeat.start()

        try:
            result = await asyncio.to_thread(
                operation
            )

            if heartbeat.lost:
                return GuardedExecutionResult(
                    result=None,
                    ownership_lost=True,
                    error=(
                        "Execution ownership işlem "
                        "sırasında kaybedildi"
                    ),
                )

            return GuardedExecutionResult(
                result=result,
                ownership_lost=False,
                error=None,
            )
        except ExecutionOwnershipLost as exc:
            return GuardedExecutionResult(
                result=None,
                ownership_lost=True,
                error=str(exc),
            )
        except Exception as exc:
            return GuardedExecutionResult(
                result=None,
                ownership_lost=False,
                error=str(exc),
            )
        finally:
            await heartbeat.stop()
