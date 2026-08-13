import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from aslan_ozaslan.jobs import JobQueue,JobStatus,IdempotencyStore
from aslan_ozaslan.cache import MemoryCache
from aslan_ozaslan.database.postgres_contract import build_postgres_migration_plan,validate_postgres_dsn
from aslan_ozaslan.admin import AdminDashboard
from aslan_ozaslan.admin.web import render_admin_snapshot
class ProductionCoreTests(unittest.TestCase):
    def test_job_queue(self):
        q=JobQueue(); out=[]; q.enqueue('sync',{'id':1}); j=q.run_next({'sync':lambda p:out.append(p['id'])}); self.assertEqual(j.status,JobStatus.SUCCEEDED); self.assertEqual(out,[1])
    def test_idempotency(self):
        s=IdempotencyStore(); a=s.fingerprint('sync',{'b':2,'a':1}); b=s.fingerprint('sync',{'a':1,'b':2}); self.assertEqual(a,b); s.record(a,{'ok':1}); self.assertTrue(s.seen(b))
    def test_cache(self):
        c=MemoryCache(); c.set('a',1,30); self.assertEqual(c.get('a'),1); c.delete('a'); self.assertIsNone(c.get('a'))
    def test_postgres_plan(self):
        self.assertIn('monitor-and-rollback-if-needed',build_postgres_migration_plan().ordered_steps)
        with self.assertRaises(ValueError): validate_postgres_dsn('sqlite:///x')
    def test_admin_html(self):
        s=AdminDashboard().build(provider_status='healthy',champion_model='m2',pending_fixtures=1,unsettled_predictions=2,drift_alerts=0,release_ready=True)
        self.assertIn('Şampiyon model',render_admin_snapshot(s))
if __name__=='__main__': unittest.main()
