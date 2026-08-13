from collections import defaultdict,deque
from .contracts import BrokerMessage
class InMemoryBroker:
    def __init__(self): self.q=defaultdict(deque); self.o=defaultdict(int); self.c={}
    def publish(self,*,topic,key,value,headers=None):
        off=self.o[topic]; self.o[topic]+=1; self.q[topic].append(BrokerMessage(topic,0,off,key,dict(value),dict(headers or {})))
    def poll(self,max_messages=100):
        out=[]
        for t in sorted(self.q):
            while self.q[t] and len(out)<max_messages: out.append(self.q[t].popleft())
        return tuple(out)
    def commit(self,m): self.c[(m.topic,m.partition)]=m.offset
