from __future__ import annotations
from dataclasses import dataclass
import hashlib,hmac,json,time
@dataclass(frozen=True)
class MVPUser:
    user_id:str;username:str;display_name:str;role:str;password_hash:str;created_at:int
@dataclass(frozen=True)
class MVPSession:
    token:str;user_id:str;username:str;display_name:str;role:str;expires_at:int
class MVPAuthError(RuntimeError): pass
class RedisMVPAuthRepository:
    def __init__(self,client,*,prefix='aslan:mvp-auth',ttl_seconds=86400):self.client=client;self.prefix=prefix;self.ttl_seconds=ttl_seconds
    def save_user(self,u):
        key=f'{self.prefix}:user:{u.username}';value=json.dumps(u.__dict__,ensure_ascii=False)
        if hasattr(self.client,'setex'):self.client.setex(key,31536000,value)
        elif hasattr(self.client,'set'):self.client.set(key,value)
        else:self.client.values[key]=value
        return u
    def get_user(self,username):
        p=self.client.get(f'{self.prefix}:user:{username}')
        if p is None:return None
        if isinstance(p,bytes):p=p.decode()
        return MVPUser(**json.loads(p))
    def save_session(self,s):
        key=f'{self.prefix}:session:{s.token}';value=json.dumps(s.__dict__,ensure_ascii=False)
        if hasattr(self.client,'setex'):self.client.setex(key,self.ttl_seconds,value)
        elif hasattr(self.client,'set'):self.client.set(key,value)
        else:self.client.values[key]=value
        return s
    def get_session(self,token):
        p=self.client.get(f'{self.prefix}:session:{token}')
        if p is None:return None
        if isinstance(p,bytes):p=p.decode()
        s=MVPSession(**json.loads(p));return s if s.expires_at>=int(time.time()) else None
    def delete_session(self,token):
        k=f'{self.prefix}:session:{token}'
        if hasattr(self.client,'delete'):self.client.delete(k)
        else:self.client.values.pop(k,None)
class MVPAuthService:
    def __init__(self,*,repository,secret):self.repository=repository;self.secret=secret
    def _hash(self,p):return hmac.new(self.secret.encode(),p.encode(),hashlib.sha256).hexdigest()
    def ensure_demo_users(self,now=None):
        t=int(now if now is not None else time.time())
        for un,dn,role,pw in [('admin','Aslan Admin','ADMIN','admin123'),('coach','Teknik Direktör','COACH','coach123'),('analyst','Maç Analisti','ANALYST','analyst123')]:
            if self.repository.get_user(un) is None:self.repository.save_user(MVPUser(f'user-{un}',un,dn,role,self._hash(pw),t))
    def login(self,*,username,password,now=None):
        u=self.repository.get_user(username)
        if u is None or not hmac.compare_digest(u.password_hash,self._hash(password)):raise MVPAuthError('Kullanıcı adı veya parola hatalı')
        t=int(now if now is not None else time.time());token=hashlib.sha256(f'{u.user_id}:{t}:{self.secret}'.encode()).hexdigest()
        return self.repository.save_session(MVPSession(token,u.user_id,u.username,u.display_name,u.role,t+86400))
    def require_session(self,token):
        s=self.repository.get_session(token)
        if s is None:raise MVPAuthError('Geçersiz veya süresi dolmuş oturum')
        return s
    def logout(self,token):self.repository.delete_session(token)
