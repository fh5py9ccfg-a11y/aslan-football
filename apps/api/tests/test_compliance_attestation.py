from dataclasses import dataclass
from apps.api.app.compliance_attestation import ComplianceAttestationService, RedisComplianceAttestationRepository

class Redis:
    def __init__(self): self.values={}; self.sets={}
    def setex(self,k,t,v): self.values[k]=v
    def get(self,k): return self.values.get(k)
    def sadd(self,k,v): self.sets.setdefault(k,set()).add(v)
    def smembers(self,k): return self.sets.get(k,set())

@dataclass
class Change:
    change_id:str='c1'; release_id:str='r1'; tenant_id:str='t1'; title:str='Title'; description:str='Desc'; change_type:str='NORMAL'; risk_level:str='LOW'; owner:str='o'; rollback_plan:str='rollback plan'; test_evidence:tuple=('tests',); status:str='APPROVED'; created_at:int=1; updated_at:int=2
@dataclass
class Evidence:
    evidence_id:str='e1'; change_id:str='c1'; release_id:str='r1'; manifest_sha256:str='a'*64; sbom_sha256:str='b'*64; test_summary:str='ok'; verification_session_id:str='v1'; safety_decision_id:str='s1'; generated_at:int=3; evidence_sha256:str='c'*64
@dataclass
class Compliance:
    change_id:str='c1'; release_id:str='r1'; approved:bool=True; rollback_plan_present:bool=True; tests_present:bool=True; evidence_present:bool=True; verification_present:bool=True; safety_decision_present:bool=True; compliant:bool=True; gaps:tuple=(); generated_at:int=4
class Repo:
    def __init__(self): self.change=Change(); self.evidence=Evidence(); self.compliance=Compliance()
    def get_change(self,x): return self.change
    def get_evidence(self,x): return self.evidence
    def get_compliance(self,x): return self.compliance
class ChangeService:
    def __init__(self): self.repository=Repo()

def build():
    cs=ChangeService()
    s=ComplianceAttestationService(repository=RedisComplianceAttestationRepository(Redis(),prefix='att'), change_management_service=cs, signing_keys={'k1':'secret'}, active_key_id='k1')
    return s,cs

def test_attestation_verifies():
    service,_=build()
    item=service.attest(attestation_id='a1',change_id='c1',issued_by='sec',now=10)
    result=service.verify(attestation_id='a1')
    assert len(item.signature)==64
    assert result['valid'] is True

def test_evidence_tampering_is_detected():
    service,cs=build(); service.attest(attestation_id='a1',change_id='c1',issued_by='sec',now=10)
    cs.repository.evidence=Evidence(test_summary='tampered')
    result=service.verify(attestation_id='a1')
    assert result['valid'] is False
    assert result['evidence_valid'] is False

def test_audit_chain_verifies():
    service,_=build()
    service.append_event(change_id='c1',event_type='ONE',payload={'x':1},now=1)
    service.append_event(change_id='c1',event_type='TWO',payload={'x':2},now=2)
    result=service.verify_chain(change_id='c1')
    assert result['valid'] is True
    assert result['entries']==2

def test_export_bundle_contains_attestation_and_chain():
    service,_=build(); service.attest(attestation_id='a1',change_id='c1',issued_by='sec',now=10)
    bundle=service.export_bundle(change_id='c1')
    assert bundle['attestation']['attestation_id']=='a1'
    assert bundle['chain_verification']['valid'] is True
