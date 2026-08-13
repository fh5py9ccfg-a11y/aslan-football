import pytest
from dataclasses import dataclass
from apps.api.app.compliance_attestation import ComplianceAttestationError, ComplianceAttestationService, RedisComplianceAttestationRepository
class Redis:
    def __init__(self): self.values={}; self.sets={}
    def setex(self,k,t,v): self.values[k]=v
    def get(self,k): return self.values.get(k)
    def sadd(self,k,v): self.sets.setdefault(k,set()).add(v)
    def smembers(self,k): return self.sets.get(k,set())
@dataclass
class Change: release_id:str='r1'
@dataclass
class Compliance: compliant:bool=False
class Repo:
    def get_change(self,x): return Change()
    def get_evidence(self,x): return object()
    def get_compliance(self,x): return Compliance()
class ChangeService: repository=Repo()
def test_non_compliant_change_cannot_be_attested():
    service=ComplianceAttestationService(repository=RedisComplianceAttestationRepository(Redis()), change_management_service=ChangeService(), signing_keys={'k':'s'}, active_key_id='k')
    with pytest.raises(ComplianceAttestationError):
        service.attest(attestation_id='a',change_id='c',issued_by='x')
