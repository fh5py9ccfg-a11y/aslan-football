import sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from aslan_ozaslan.broker_v6 import *
class T(unittest.TestCase):
 def test_worker(self):
  with tempfile.TemporaryDirectory() as d:
   b=InMemoryBroker(); b.publish(topic='in',key='k',value={'x':1}); r=InboxOutboxRepository(Path(d)/'x.db'); w=BrokerWorker(consumer=b,producer=b,repository=r,handler=lambda m:({'topic':'out','key':m.key,'value':{'ok':1}},)); rep=w.run_once(); self.assertEqual(rep.processed,1); self.assertEqual(rep.outbox_published,1); self.assertEqual(r.counts()['completed'],1)
 def test_dead_letter(self):
  with tempfile.TemporaryDirectory() as d:
   b=InMemoryBroker(); b.publish(topic='in',key='k',value={}); r=InboxOutboxRepository(Path(d)/'x.db'); rep=BrokerWorker(consumer=b,producer=b,repository=r,handler=lambda m:(_ for _ in ()).throw(ValueError('bad'))).run_once(); self.assertEqual(rep.failed,1); self.assertEqual(r.counts()['dead_letter'],1)
if __name__=='__main__':unittest.main()
