import asyncio
from apps.api.app.alerting import (
    AlertDeliveryService, AlertMessage, AlertSubscription,
    RedisAlertRepository, WebhookDeliveryClient,
)

class Redis:
    def __init__(self):
        self.values, self.sets, self.lists = {}, {}, {}
    def setex(self,k,t,v): self.values[k]=v
    def get(self,k): return self.values.get(k)
    def sadd(self,k,v): self.sets.setdefault(k,set()).add(v)
    def smembers(self,k): return self.sets.get(k,set())
    def rpush(self,k,v): self.lists.setdefault(k,[]).append(v)
    def lrange(self,k,s,e): return self.lists.get(k,[])[s:e+1]

def subscription(minimum="MEDIUM"):
    return AlertSubscription("s1","tenant-a","m1","MOMENTUM_SHIFT",minimum,"https://example.test",True,100)

def alert(severity="HIGH"):
    return AlertMessage("a1","tenant-a","m1","MOMENTUM_SHIFT",severity,"Title","Body",{},100)

def test_matching_subscription():
    repo=RedisAlertRepository(Redis(),prefix="a")
    repo.save_subscription(subscription())
    assert len(repo.matching_subscriptions(alert()))==1

def test_successful_delivery():
    repo=RedisAlertRepository(Redis(),prefix="a"); repo.save_subscription(subscription())
    async def sender(destination,payload): return 202
    svc=AlertDeliveryService(repository=repo,client=WebhookDeliveryClient(sender),max_attempts=3,backoff_seconds=0)
    result=asyncio.run(svc.publish(alert()))
    assert result["delivered"]==1
    assert len(repo.list_attempts("a1"))==1

def test_dead_letter_after_failures():
    repo=RedisAlertRepository(Redis(),prefix="a"); repo.save_subscription(subscription())
    async def sender(destination,payload): return 500
    svc=AlertDeliveryService(repository=repo,client=WebhookDeliveryClient(sender),max_attempts=2,backoff_seconds=0)
    result=asyncio.run(svc.publish(alert()))
    assert result["failed"]==1
    assert len(repo.list_attempts("a1"))==2
    assert len(repo.list_dead_letters())==1
