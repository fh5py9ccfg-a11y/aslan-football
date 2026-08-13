from __future__ import annotations
from dataclasses import dataclass
import json
import time

class SplitBrainRisk(RuntimeError):
    pass

class PromotionRejected(RuntimeError):
    pass

@dataclass(frozen=True)
class RegionCheckpoint:
    region: str
    role: str
    epoch: int
    replication_cursor: int
    source_timestamp: int
    applied_timestamp: int
    rpo_seconds: int
    updated_at: int

@dataclass(frozen=True)
class PromotionResult:
    region: str
    previous_primary: str | None
    new_epoch: int
    promoted_at: int
    rpo_seconds: int
    status: str

class RedisDisasterRecoveryRepository:
    PROMOTE_SCRIPT = '''
    local topology_key = KEYS[1]
    local checkpoint_key = KEYS[2]
    local expected_epoch = tonumber(ARGV[1])
    local region = ARGV[2]
    local now = tonumber(ARGV[3])
    local payload = ARGV[4]

    local topology_raw = redis.call("GET", topology_key)
    local topology = nil
    if topology_raw then
        topology = cjson.decode(topology_raw)
        local current_epoch = tonumber(topology.epoch or 0)
        if current_epoch ~= expected_epoch then
            return {-1, current_epoch}
        end
        if topology.primary_region == region then
            return {0, topology_raw}
        end
    end

    redis.call("SET", topology_key, payload)
    redis.call("SET", checkpoint_key, payload)
    return {1, payload}
    '''

    def __init__(
        self,
        client,
        *,
        prefix: str = "aslan:dr",
        max_rpo_seconds: int = 60,
    ):
        if max_rpo_seconds < 0:
            raise ValueError("max_rpo_seconds negatif olamaz")
        self.client = client
        self.prefix = prefix
        self.max_rpo_seconds = max_rpo_seconds

    def save_checkpoint(
        self,
        *,
        region: str,
        role: str,
        epoch: int,
        replication_cursor: int,
        source_timestamp: int,
        applied_timestamp: int,
        now: int | None = None,
    ) -> RegionCheckpoint:
        current = int(now if now is not None else time.time())
        checkpoint = RegionCheckpoint(
            region=region,
            role=role,
            epoch=epoch,
            replication_cursor=replication_cursor,
            source_timestamp=source_timestamp,
            applied_timestamp=applied_timestamp,
            rpo_seconds=max(0, source_timestamp - applied_timestamp),
            updated_at=current,
        )
        self.client.set(
            self._checkpoint_key(region),
            self._serialize(checkpoint),
        )
        return checkpoint

    def get_checkpoint(
        self,
        region: str,
    ) -> RegionCheckpoint | None:
        payload = self.client.get(self._checkpoint_key(region))
        if payload is None:
            return None
        return self._deserialize_checkpoint(payload)

    def topology(self) -> dict:
        payload = self.client.get(self._topology_key())
        if payload is None:
            return {
                "primary_region": None,
                "epoch": 0,
                "promoted_at": None,
            }
        if isinstance(payload, bytes):
            payload = payload.decode("utf-8")
        return json.loads(payload)

    def promote(
        self,
        *,
        region: str,
        expected_epoch: int,
        now: int | None = None,
    ) -> PromotionResult:
        current = int(now if now is not None else time.time())
        checkpoint = self.get_checkpoint(region)
        if checkpoint is None:
            raise PromotionRejected("Bölgesel checkpoint bulunamadı")
        if checkpoint.rpo_seconds > self.max_rpo_seconds:
            raise PromotionRejected(
                f"RPO sınırı aşıldı: {checkpoint.rpo_seconds}s"
            )

        topology = self.topology()
        previous_primary = topology.get("primary_region")
        new_epoch = expected_epoch + 1
        payload = json.dumps(
            {
                "primary_region": region,
                "previous_primary": previous_primary,
                "epoch": new_epoch,
                "promoted_at": current,
                "rpo_seconds": checkpoint.rpo_seconds,
            },
            ensure_ascii=False,
            separators=(",", ":"),
        )
        result = self.client.eval(
            self.PROMOTE_SCRIPT,
            2,
            self._topology_key(),
            self._checkpoint_key(region),
            expected_epoch,
            region,
            current,
            payload,
        )
        code = int(result[0])
        if code == -1:
            raise SplitBrainRisk(
                "Topology epoch değişti; promotion reddedildi"
            )
        if code == 0:
            existing = self.topology()
            return PromotionResult(
                region=region,
                previous_primary=existing.get("previous_primary"),
                new_epoch=int(existing.get("epoch", new_epoch)),
                promoted_at=int(existing.get("promoted_at", current)),
                rpo_seconds=int(existing.get("rpo_seconds", checkpoint.rpo_seconds)),
                status="ALREADY_PRIMARY",
            )

        return PromotionResult(
            region=region,
            previous_primary=previous_primary,
            new_epoch=new_epoch,
            promoted_at=current,
            rpo_seconds=checkpoint.rpo_seconds,
            status="PROMOTED",
        )

    def failback(
        self,
        *,
        target_region: str,
        expected_epoch: int,
        now: int | None = None,
    ) -> PromotionResult:
        return self.promote(
            region=target_region,
            expected_epoch=expected_epoch,
            now=now,
        )

    def health(self) -> dict:
        topology = self.topology()
        primary = topology.get("primary_region")
        checkpoint = (
            self.get_checkpoint(primary)
            if primary
            else None
        )
        return {
            "primary_region": primary,
            "epoch": int(topology.get("epoch", 0)),
            "checkpoint": (
                checkpoint.__dict__
                if checkpoint is not None
                else None
            ),
            "rpo_within_target": (
                checkpoint is not None
                and checkpoint.rpo_seconds <= self.max_rpo_seconds
            ),
        }

    def _checkpoint_key(self, region: str) -> str:
        return f"{self.prefix}:checkpoint:{region}"

    def _topology_key(self) -> str:
        return f"{self.prefix}:topology"

    @staticmethod
    def _serialize(item: RegionCheckpoint) -> str:
        return json.dumps(
            item.__dict__,
            ensure_ascii=False,
            separators=(",", ":"),
        )

    @staticmethod
    def _deserialize_checkpoint(payload) -> RegionCheckpoint:
        if isinstance(payload, bytes):
            payload = payload.decode("utf-8")
        return RegionCheckpoint(**json.loads(payload))
