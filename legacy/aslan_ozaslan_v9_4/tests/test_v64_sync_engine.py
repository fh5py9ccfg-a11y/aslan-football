import sys,unittest,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from aslan_ozaslan.sync_v6 import *
from aslan_ozaslan.admin.sync_dashboard_page import render_sync_dashboard_page
class FakeConfig: per_page=50
class FakeClient:
    def __init__(self,payloads): self.payloads=list(payloads); self.config=FakeConfig(); self.calls=[]
    def _get(self,path,params): self.calls.append((path,dict(params))); return self.payloads.pop(0)
class T(unittest.TestCase):
    def fixture(self,i): return {'id':i,'starting_at':'2026-07-31T18:00:00+00:00','participants':[{'id':1},{'id':2}],'scores':[{'score':{'goals':1}},{'score':{'goals':0}}],'events':[{'minute':10},{'minute':50}]}
    def test_rate_cache(self):
        l=RateLimitManager(capacity=1,refill_per_second=1); self.assertTrue(l.acquire().allowed); self.assertFalse(l.acquire().allowed)
        c=ConditionalRequestCache(); c.update('x',etag='"a"',last_modified='d',payload={'id':1}); self.assertEqual(c.request_headers('x')['If-None-Match'],'"a"'); self.assertEqual(c.resolve_not_modified('x')['id'],1)
    def test_integrity(self):
        v=FixtureIntegrityValidator(); self.assertTrue(v.validate(self.fixture(1)).valid); bad=self.fixture(2); bad['events']=[{'minute':70},{'minute':20}]; self.assertIn('event_order_invalid',v.validate(bad).errors)
    def test_sync(self):
        with tempfile.TemporaryDirectory() as t:
            client=FakeClient([{'data':[self.fixture(1)],'pagination':{'has_more':True}},{'data':[self.fixture(2)],'pagination':{'has_more':False}}])
            repo=SyncCheckpointRepository(Path(t)/'sync.json'); engine=IncrementalFixtureSyncEngine(provider_name='sportmonks',client=client,checkpoint_repository=repo,rate_limit=RateLimitManager(capacity=10,refill_per_second=10))
            r=engine.sync_date('2026-07-31'); self.assertTrue(r.completed); self.assertEqual(r.metrics.fixtures_updated,2); self.assertEqual(repo.load('sportmonks','fixtures:2026-07-31').page,2); self.assertIn('Production Data Sync',render_sync_dashboard_page(r))
if __name__=='__main__': unittest.main()
