import pytest
from apps.api.app.change_management import ChangeManagementService, RedisChangeManagementRepository, ChangeManagementValidationError
class Redis:
    def __init__(self): self.values,self.sets={},{}
    def setex(self,k,t,v): self.values[k]=v
    def get(self,k): return self.values.get(k)
    def sadd(self,k,v): self.sets.setdefault(k,set()).add(v)
    def smembers(self,k): return self.sets.get(k,set())
class R:
    def get_session(self,s): return None
    def list_decisions(self,t,limit=100): return ()
class D: repository=R()
def service(): return ChangeManagementService(repository=RedisChangeManagementRepository(Redis()),deployment_verification_service=D(),deployment_safety_service=D())
def test_requires_rollback_and_tests():
    with pytest.raises(ChangeManagementValidationError):
        service().create_change(change_id='c',tenant_id='t',release_id='r',title='Deploy update',description='A sufficiently long description',change_type='NORMAL',risk_level='LOW',owner='o',rollback_plan='short',test_evidence=('x',))
    with pytest.raises(ChangeManagementValidationError):
        service().create_change(change_id='c',tenant_id='t',release_id='r',title='Deploy update',description='A sufficiently long description',change_type='NORMAL',risk_level='LOW',owner='o',rollback_plan='Rollback to previous version',test_evidence=())
