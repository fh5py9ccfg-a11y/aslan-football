from apps.api.app.mvp_auth import MVPAuthError,MVPAuthService,RedisMVPAuthRepository
class Redis:
 def __init__(self):self.values={}
 def setex(self,k,t,v):self.values[k]=v
 def get(self,k):return self.values.get(k)
 def delete(self,k):self.values.pop(k,None)
def build():
 s=MVPAuthService(repository=RedisMVPAuthRepository(Redis(),prefix='a'),secret='secret');s.ensure_demo_users(now=100);return s
def test_login_and_restore():
 import time
 s=build();x=s.login(username='coach',password='coach123',now=int(time.time()));assert s.require_session(x.token).role=='COACH'
def test_bad_password():
 s=build()
 try:s.login(username='coach',password='bad',now=101)
 except MVPAuthError:pass
 else:raise AssertionError('MVPAuthError bekleniyordu')
