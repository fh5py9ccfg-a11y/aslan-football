from dataclasses import dataclass
from apps.api.app.change_management import ChangeManagementService, RedisChangeManagementRepository
class Redis:
    def __init__(self): self.values,self.sets={},{}
    def setex(self,k,t,v): self.values[k]=v
    def get(self,k): return self.values.get(k)
    def sadd(self,k,v): self.sets.setdefault(k,set()).add(v)
    def smembers(self,k): return self.sets.get(k,set())
@dataclass
class Verification: session_id:str='v1'
class VR: 
    def get_session(self,s): return Verification()
class VS: repository=VR()
@dataclass
class Decision: decision_id:str='s1'
class SR:
    def list_decisions(self,t,limit=100): return (Decision(),)
class SS: repository=SR()
def build(): return ChangeManagementService(repository=RedisChangeManagementRepository(Redis(),prefix='c'),deployment_verification_service=VS(),deployment_safety_service=SS())
def test_lifecycle_and_compliance():
    s=build(); s.create_change(change_id='c1',tenant_id='t',release_id='r',title='Deploy update',description='Deploy calibrated prediction model',change_type='NORMAL',risk_level='LOW',owner='o',rollback_plan='Rollback to previous champion',test_evidence=('245 tests passed',),now=1)
    assert s.submit(change_id='c1',now=2).status=='IN_REVIEW'
    s.approve(approval_id='a1',change_id='c1',role='ops',actor='ops',decision='APPROVED',comment='ready',now=3)
    assert s.approve(approval_id='a2',change_id='c1',role='security',actor='sec',decision='APPROVED',comment='secure',now=4)[0].status=='APPROVED'
    e=s.generate_evidence(evidence_id='e1',change_id='c1',manifest_sha256='a'*64,sbom_sha256='b'*64,test_summary='245 passed',verification_session_id='v1',safety_decision_id='s1',now=5)
    assert len(e.evidence_sha256)==64
    assert s.compliance(change_id='c1',now=6).compliant is True
