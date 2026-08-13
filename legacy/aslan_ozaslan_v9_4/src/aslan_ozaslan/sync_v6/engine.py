import time
from .domain import SyncCursor,SyncMetrics,SyncRunReport
from .integrity import FixtureIntegrityValidator
class IncrementalFixtureSyncEngine:
    def __init__(self,*,provider_name,client,checkpoint_repository,rate_limit,validator=None):
        self.provider_name=provider_name; self.client=client; self.checkpoints=checkpoint_repository; self.rate_limit=rate_limit; self.validator=validator or FixtureIntegrityValidator()
    def sync_date(self,date):
        resource=f'fixtures:{date}'; cursor=self.checkpoints.load(self.provider_name,resource)
        req=ok=fail=seen=updated=skipped=0; lats=[]; errors=[]; page=cursor.page; completed=False
        while True:
            if not self.rate_limit.acquire().allowed: break
            started=time.perf_counter(); req+=1
            try:
                payload=self.client._get(f'/fixtures/date/{date}',{'include':'participants;state;scores;events','per_page':self.client.config.per_page,'page':page}); ok+=1
            except Exception:
                fail+=1; break
            finally: lats.append((time.perf_counter()-started)*1000)
            for fixture in payload.get('data') or []:
                seen+=1; result=self.validator.validate(fixture)
                if result.valid: updated+=1
                else:
                    skipped+=1; errors.extend(f"{fixture.get('id')}:{e}" for e in result.errors)
            more=bool((payload.get('pagination') or {}).get('has_more',False))
            if more:
                page+=1; cursor=SyncCursor(self.provider_name,resource,page,cursor.updated_since,False); self.checkpoints.save(cursor); continue
            completed=True; cursor=SyncCursor(self.provider_name,resource,page,date,True); self.checkpoints.save(cursor); break
        metrics=SyncMetrics(req,ok,fail,seen,updated,skipped,sum(lats)/len(lats) if lats else 0.0)
        return SyncRunReport(cursor,metrics,tuple(errors),completed)
