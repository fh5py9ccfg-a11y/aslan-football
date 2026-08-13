from __future__ import annotations
from dataclasses import dataclass
import json
import time

class UpgradeConflict(RuntimeError):
    pass

class IncompatibleRelease(RuntimeError):
    pass

@dataclass(frozen=True)
class UpgradeState:
    rollout_id: str
    source_version: str
    target_version: str
    status: str
    stage: str
    traffic_percent: int
    expected_generation: int
    current_generation: int
    started_at: int
    updated_at: int
    rollback_reason: str | None
    schema_compatible: bool

class VersionCompatibility:
    @staticmethod
    def major(version: str) -> int:
        return int(version.split('.', 1)[0])

    @classmethod
    def validate(cls, *, source_version: str, target_version: str, schema_compatible: bool) -> None:
        source_major = cls.major(source_version)
        target_major = cls.major(target_version)
        if target_major < source_major:
            raise IncompatibleRelease('Hedef major sürüm kaynak sürümden eski olamaz')
        if not schema_compatible:
            raise IncompatibleRelease('Şema uyumluluk kontrolü başarısız')

class RedisRollingUpgradeRepository:
    UPDATE_SCRIPT = '''
    local key = KEYS[1]
    local expected_generation = tonumber(ARGV[1])
    local payload = ARGV[2]
    local raw = redis.call("GET", key)
    if raw then
        local current = cjson.decode(raw)
        if tonumber(current.current_generation) ~= expected_generation then
            return {0, raw}
        end
    elseif expected_generation ~= 0 then
        return {0, "missing"}
    end
    redis.call("SET", key, payload)
    return {1, payload}
    '''
    def __init__(self, client, *, prefix='aslan:rolling-upgrade'):
        self.client = client
        self.prefix = prefix
    def get(self, rollout_id: str):
        payload = self.client.get(self._key(rollout_id))
        return None if payload is None else self._deserialize(payload)
    def save(self, state: UpgradeState):
        result = self.client.eval(self.UPDATE_SCRIPT, 1, self._key(state.rollout_id), state.expected_generation, self._serialize(state))
        if int(result[0]) != 1:
            raise UpgradeConflict('Rolling upgrade generation değişti')
        return state
    def _key(self, rollout_id: str) -> str:
        return f'{self.prefix}:{rollout_id}'
    @staticmethod
    def _serialize(state: UpgradeState) -> str:
        return json.dumps(state.__dict__, ensure_ascii=False, separators=(',', ':'))
    @staticmethod
    def _deserialize(payload):
        if isinstance(payload, bytes):
            payload = payload.decode('utf-8')
        return UpgradeState(**json.loads(payload))

class RollingUpgradeCoordinator:
    STAGES = (('VALIDATING', 0), ('CANARY', 5), ('EXPANDING', 25), ('MAJORITY', 50), ('FULL', 100))
    def __init__(self, *, repository):
        self.repository = repository
    def start(self, *, rollout_id: str, source_version: str, target_version: str, schema_compatible: bool, now: int | None = None):
        VersionCompatibility.validate(source_version=source_version, target_version=target_version, schema_compatible=schema_compatible)
        current = int(now if now is not None else time.time())
        return self.repository.save(UpgradeState(rollout_id, source_version, target_version, 'IN_PROGRESS', 'VALIDATING', 0, 0, 1, current, current, None, schema_compatible))
    def advance(self, rollout_id: str, *, health_ok: bool, now: int | None = None):
        state = self._required(rollout_id)
        if state.status != 'IN_PROGRESS':
            return state
        if not health_ok:
            return self.rollback(rollout_id, reason='Health gate başarısız', now=now)
        names = [stage[0] for stage in self.STAGES]
        index = names.index(state.stage)
        if index >= len(self.STAGES) - 1:
            return self._replace(state, status='COMPLETED', stage='FULL', traffic_percent=100, now=now)
        stage, traffic = self.STAGES[index + 1]
        return self._replace(state, status='COMPLETED' if stage == 'FULL' else 'IN_PROGRESS', stage=stage, traffic_percent=traffic, now=now)
    def rollback(self, rollout_id: str, *, reason: str, now: int | None = None):
        return self._replace(self._required(rollout_id), status='ROLLED_BACK', stage='ROLLBACK', traffic_percent=0, rollback_reason=reason[:1000], now=now)
    def status(self, rollout_id: str):
        return self.repository.get(rollout_id)
    def _required(self, rollout_id: str):
        state = self.repository.get(rollout_id)
        if state is None:
            raise KeyError('Rolling upgrade kaydı bulunamadı')
        return state
    def _replace(self, state: UpgradeState, *, status: str, stage: str, traffic_percent: int, now: int | None = None, rollback_reason: str | None = None):
        current = int(now if now is not None else time.time())
        return self.repository.save(UpgradeState(state.rollout_id, state.source_version, state.target_version, status, stage, traffic_percent, state.current_generation, state.current_generation + 1, state.started_at, current, rollback_reason, state.schema_compatible))
