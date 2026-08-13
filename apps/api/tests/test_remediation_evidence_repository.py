import json
import pytest

from apps.api.app.distributed_lease import (
    StaleFencingToken,
)
from apps.api.app.quarantine_verification import (
    RemediationEvidence,
    RedisRemediationEvidenceRepository,
)

class Redis:
    def __init__(self):
        self.values = {"fence": 5}

    def eval(self, script, number_of_keys, *args):
        evidence_key, fence_key = args[:2]
        token = int(args[2])
        payload = args[3]
        current = int(self.values.get(fence_key, 0))
        if token < current:
            return [-1, current]
        self.values[fence_key] = token
        self.values[evidence_key] = payload
        return [1, token]

    def get(self, key):
        return self.values.get(key)

def evidence(token):
    return RemediationEvidence(
        claim_id="c1",
        index_key="index-a",
        phase="subject",
        retry_status="SUCCEEDED",
        pre_orphans=1,
        post_orphans=0,
        pre_live=1,
        post_live=1,
        pre_ttl=-1,
        post_ttl=120,
        verified=True,
        reason="healthy",
        operator="admin",
        fencing_token=token,
        created_at=100,
    )

def test_evidence_save_load_and_stale_rejection():
    redis = Redis()
    repo = RedisRemediationEvidenceRepository(
        redis,
        prefix="remediation",
        fence_key="fence",
    )

    repo.save(evidence(6))
    loaded = repo.get("c1")
    assert loaded is not None
    assert loaded.verified is True

    with pytest.raises(StaleFencingToken):
        repo.save(evidence(4))
