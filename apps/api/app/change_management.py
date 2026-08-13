from __future__ import annotations
from dataclasses import dataclass
import hashlib, json, time

@dataclass(frozen=True)
class ChangeRequest:
    change_id:str; tenant_id:str; release_id:str; title:str; description:str
    change_type:str; risk_level:str; owner:str; rollback_plan:str
    test_evidence:tuple[str,...]; status:str; created_at:int; updated_at:int

@dataclass(frozen=True)
class ChangeApproval:
    approval_id:str; change_id:str; role:str; actor:str; decision:str; comment:str; decided_at:int

@dataclass(frozen=True)
class ReleaseEvidence:
    evidence_id:str; change_id:str; release_id:str; manifest_sha256:str; sbom_sha256:str
    test_summary:str; verification_session_id:str; safety_decision_id:str
    generated_at:int; evidence_sha256:str

@dataclass(frozen=True)
class ComplianceSnapshot:
    change_id:str; release_id:str; approved:bool; rollback_plan_present:bool
    tests_present:bool; evidence_present:bool; verification_present:bool
    safety_decision_present:bool; compliant:bool; gaps:tuple[str,...]; generated_at:int

class ChangeManagementError(RuntimeError): pass
class ChangeManagementValidationError(ValueError): pass

class RedisChangeManagementRepository:
    def __init__(self, client, *, prefix='aslan:change-management', ttl_seconds=31536000):
        self.client,self.prefix,self.ttl_seconds=client,prefix,ttl_seconds
    def save_change(self,c):
        d={**c.__dict__,'test_evidence':list(c.test_evidence)}
        self.client.setex(f'{self.prefix}:change:{c.change_id}',self.ttl_seconds,json.dumps(d,ensure_ascii=False,separators=(',',':')))
        self.client.sadd(f'{self.prefix}:changes:{c.tenant_id}',c.change_id); return c
    def get_change(self,change_id):
        p=self.client.get(f'{self.prefix}:change:{change_id}')
        if p is None:return None
        if isinstance(p,bytes):p=p.decode()
        d=json.loads(p); d['test_evidence']=tuple(d['test_evidence']); return ChangeRequest(**d)
    def list_changes(self,tenant_id,*,limit=100):
        items=[]
        for cid in self.client.smembers(f'{self.prefix}:changes:{tenant_id}'):
            if isinstance(cid,bytes):cid=cid.decode()
            c=self.get_change(str(cid))
            if c: items.append(c)
        items.sort(key=lambda x:x.created_at,reverse=True); return tuple(items[:limit])
    def save_approval(self,a):
        self.client.setex(f'{self.prefix}:approval:{a.approval_id}',self.ttl_seconds,json.dumps(a.__dict__,ensure_ascii=False,separators=(',',':')))
        self.client.sadd(f'{self.prefix}:approvals:{a.change_id}',a.approval_id); return a
    def list_approvals(self,change_id):
        items=[]
        for aid in self.client.smembers(f'{self.prefix}:approvals:{change_id}'):
            if isinstance(aid,bytes):aid=aid.decode()
            p=self.client.get(f'{self.prefix}:approval:{aid}')
            if p is None: continue
            if isinstance(p,bytes):p=p.decode()
            items.append(ChangeApproval(**json.loads(p)))
        items.sort(key=lambda x:x.decided_at); return tuple(items)
    def save_evidence(self,e):
        self.client.setex(f'{self.prefix}:evidence:{e.change_id}',self.ttl_seconds,json.dumps(e.__dict__,ensure_ascii=False,separators=(',',':'))); return e
    def get_evidence(self,change_id):
        p=self.client.get(f'{self.prefix}:evidence:{change_id}')
        if p is None:return None
        if isinstance(p,bytes):p=p.decode()
        return ReleaseEvidence(**json.loads(p))
    def save_compliance(self,s):
        d={**s.__dict__,'gaps':list(s.gaps)}
        self.client.setex(f'{self.prefix}:compliance:{s.change_id}',self.ttl_seconds,json.dumps(d,ensure_ascii=False,separators=(',',':'))); return s
    def get_compliance(self,change_id):
        p=self.client.get(f'{self.prefix}:compliance:{change_id}')
        if p is None:return None
        if isinstance(p,bytes):p=p.decode()
        d=json.loads(p); d['gaps']=tuple(d['gaps']); return ComplianceSnapshot(**d)

class ChangeManagementService:
    REQUIRED_CAB_ROLES=('ops','security')
    def __init__(self,*,repository,deployment_verification_service,deployment_safety_service):
        self.repository=repository; self.deployment_verification_service=deployment_verification_service; self.deployment_safety_service=deployment_safety_service
    def create_change(self,*,change_id,tenant_id,release_id,title,description,change_type,risk_level,owner,rollback_plan,test_evidence,now=None):
        ct=change_type.upper(); rl=risk_level.upper()
        if ct not in {'STANDARD','NORMAL','MAJOR','EMERGENCY'}: raise ChangeManagementValidationError('Geçersiz change type')
        if rl not in {'LOW','MEDIUM','HIGH','CRITICAL'}: raise ChangeManagementValidationError('Geçersiz risk level')
        if len(title.strip())<5 or len(description.strip())<10: raise ChangeManagementValidationError('Change açıklaması yetersiz')
        if len(rollback_plan.strip())<10: raise ChangeManagementValidationError('Rollback plan zorunludur')
        if not test_evidence: raise ChangeManagementValidationError('En az bir test kanıtı gereklidir')
        t=int(now if now is not None else time.time())
        return self.repository.save_change(ChangeRequest(change_id,tenant_id,release_id,title,description,ct,rl,owner,rollback_plan,test_evidence,'DRAFT',t,t))
    def submit(self,*,change_id,now=None):
        c=self._required(change_id)
        if c.status!='DRAFT': raise ChangeManagementError('Yalnızca DRAFT change submit edilebilir')
        u=ChangeRequest(**{**c.__dict__,'status':'IN_REVIEW','updated_at':int(now if now is not None else time.time())}); return self.repository.save_change(u)
    def approve(self,*,approval_id,change_id,role,actor,decision,comment,now=None):
        c=self._required(change_id)
        if c.status not in {'IN_REVIEW','APPROVED'}: raise ChangeManagementError('Change approval kabul etmiyor')
        d=decision.upper()
        if d not in {'APPROVED','REJECTED'}: raise ChangeManagementValidationError('Approval kararı geçersiz')
        if len(comment.strip())<3: raise ChangeManagementValidationError('Approval açıklaması gereklidir')
        a=ChangeApproval(approval_id,change_id,role.lower(),actor,d,comment,int(now if now is not None else time.time()))
        self.repository.save_approval(a); approvals=self.repository.list_approvals(change_id)
        rejected=any(x.decision=='REJECTED' for x in approvals); roles={x.role for x in approvals if x.decision=='APPROVED'}
        status='REJECTED' if rejected else ('APPROVED' if all(r in roles for r in self.REQUIRED_CAB_ROLES) else 'IN_REVIEW')
        u=ChangeRequest(**{**c.__dict__,'status':status,'updated_at':a.decided_at}); self.repository.save_change(u); return u,a
    def generate_evidence(self,*,evidence_id,change_id,manifest_sha256,sbom_sha256,test_summary,verification_session_id,safety_decision_id,now=None):
        c=self._required(change_id)
        if c.status!='APPROVED': raise ChangeManagementError('Release evidence yalnızca approved change için üretilebilir')
        if len(manifest_sha256)!=64 or len(sbom_sha256)!=64: raise ChangeManagementValidationError('SHA-256 geçersiz')
        v=self.deployment_verification_service.repository.get_session(verification_session_id)
        if v is None: raise KeyError('Verification session bulunamadı')
        decisions=self.deployment_safety_service.repository.list_decisions(c.tenant_id,limit=1000)
        if not any(x.decision_id==safety_decision_id for x in decisions): raise KeyError('Deployment safety decision bulunamadı')
        t=int(now if now is not None else time.time())
        canonical={'evidence_id':evidence_id,'change_id':change_id,'release_id':c.release_id,'manifest_sha256':manifest_sha256,'sbom_sha256':sbom_sha256,'test_summary':test_summary,'verification_session_id':verification_session_id,'safety_decision_id':safety_decision_id,'generated_at':t}
        digest=hashlib.sha256(json.dumps(canonical,sort_keys=True,separators=(',',':')).encode()).hexdigest()
        return self.repository.save_evidence(ReleaseEvidence(**canonical,evidence_sha256=digest))
    def compliance(self,*,change_id,now=None):
        c=self._required(change_id); approvals=self.repository.list_approvals(change_id)
        roles={x.role for x in approvals if x.decision=='APPROVED'}
        approved=c.status=='APPROVED' and all(r in roles for r in self.REQUIRED_CAB_ROLES)
        e=self.repository.get_evidence(change_id); rp=len(c.rollback_plan.strip())>=10; tp=bool(c.test_evidence); ep=e is not None
        vp=sp=False
        if e:
            vp=self.deployment_verification_service.repository.get_session(e.verification_session_id) is not None
            sp=any(x.decision_id==e.safety_decision_id for x in self.deployment_safety_service.repository.list_decisions(c.tenant_id,limit=1000))
        gaps=[]
        if not approved:gaps.append('CAB approval eksik')
        if not rp:gaps.append('Rollback plan eksik')
        if not tp:gaps.append('Test evidence eksik')
        if not ep:gaps.append('Release evidence eksik')
        if not vp:gaps.append('Deployment verification eksik')
        if not sp:gaps.append('Deployment safety decision eksik')
        s=ComplianceSnapshot(change_id,c.release_id,approved,rp,tp,ep,vp,sp,not gaps,tuple(gaps),int(now if now is not None else time.time()))
        return self.repository.save_compliance(s)
    def timeline(self,*,change_id):
        c=self._required(change_id); out=[{'type':'CHANGE_CREATED','at':c.created_at,'status':'DRAFT','actor':c.owner,'detail':c.title},{'type':'CHANGE_STATUS','at':c.updated_at,'status':c.status,'actor':c.owner,'detail':c.description}]
        for a in self.repository.list_approvals(change_id): out.append({'type':'CAB_APPROVAL','at':a.decided_at,'status':a.decision,'actor':a.actor,'detail':f'{a.role}: {a.comment}'})
        e=self.repository.get_evidence(change_id)
        if e: out.append({'type':'RELEASE_EVIDENCE','at':e.generated_at,'status':'GENERATED','actor':None,'detail':e.evidence_sha256})
        s=self.repository.get_compliance(change_id)
        if s: out.append({'type':'COMPLIANCE','at':s.generated_at,'status':'COMPLIANT' if s.compliant else 'NON_COMPLIANT','actor':None,'detail':'; '.join(s.gaps)})
        out.sort(key=lambda x:(x['at'],x['type'])); return tuple(out)
    def _required(self,change_id):
        c=self.repository.get_change(change_id)
        if c is None: raise KeyError('Change request bulunamadı')
        return c
