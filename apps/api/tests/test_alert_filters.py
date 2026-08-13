from apps.api.app.alerting import AlertMessage, AlertSubscription, RedisAlertRepository

class Redis:
    def __init__(self): self.values,self.sets={},{}
    def setex(self,k,t,v): self.values[k]=v
    def get(self,k): return self.values.get(k)
    def sadd(self,k,v): self.sets.setdefault(k,set()).add(v)
    def smembers(self,k): return self.sets.get(k,set())

def test_severity_filter():
    repo=RedisAlertRepository(Redis(),prefix="a")
    repo.save_subscription(AlertSubscription("s1","t",None,None,"HIGH","url",True,1))
    msg=AlertMessage("a","t","m","X","MEDIUM","T","B",{},1)
    assert repo.matching_subscriptions(msg)==()
