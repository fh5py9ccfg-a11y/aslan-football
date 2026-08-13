from dataclasses import dataclass
from enum import Enum
from uuid import uuid4

class JobStatus(str, Enum):
    PENDING='PENDING'; RUNNING='RUNNING'; SUCCEEDED='SUCCEEDED'; FAILED='FAILED'

@dataclass
class Job:
    job_id: str
    name: str
    payload: dict
    status: JobStatus = JobStatus.PENDING
    attempts: int = 0
    error: str | None = None

class JobQueue:
    def __init__(self): self._jobs=[]
    def enqueue(self,name,payload):
        if not name.strip(): raise ValueError('İş adı boş olamaz')
        job=Job(str(uuid4()),name,dict(payload)); self._jobs.append(job); return job
    def next_pending(self): return next((j for j in self._jobs if j.status==JobStatus.PENDING),None)
    def run_next(self,handlers):
        job=self.next_pending()
        if job is None: return None
        handler=handlers.get(job.name)
        if handler is None:
            job.status=JobStatus.FAILED; job.error=f'Handler bulunamadı: {job.name}'; return job
        job.status=JobStatus.RUNNING; job.attempts+=1
        try: handler(job.payload)
        except Exception as exc:
            job.status=JobStatus.FAILED; job.error=str(exc); return job
        job.status=JobStatus.SUCCEEDED; job.error=None; return job
    def list_jobs(self): return tuple(self._jobs)
