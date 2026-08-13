from dataclasses import dataclass
@dataclass(frozen=True)
class WorkerReport: polled:int; processed:int; duplicates:int; failed:int; outbox_published:int
class BrokerWorker:
    def __init__(self,*,consumer,producer,repository,handler): self.consumer=consumer; self.producer=producer; self.repository=repository; self.handler=handler
    def run_once(self,max_messages=100):
        msgs=self.consumer.poll(max_messages); p=d=f=0
        for m in msgs:
            if not self.repository.begin(m): d+=1; self.consumer.commit(m); continue
            try:self.repository.complete(m,self.handler(m)); self.consumer.commit(m); p+=1
            except Exception as e:self.repository.fail(m,str(e)); self.consumer.commit(m); f+=1
        pub=0
        for i in self.repository.pending(): self.producer.publish(topic=i['topic'],key=i['key'],value=i['value'],headers=i['headers']); self.repository.mark(i['id']); pub+=1
        return WorkerReport(len(msgs),p,d,f,pub)
