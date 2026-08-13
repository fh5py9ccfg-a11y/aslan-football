import json
from pathlib import Path
from .domain import SyncCursor
class SyncCheckpointRepository:
    def __init__(self,path): self.path=Path(path)
    def load(self,provider,resource):
        if not self.path.exists(): return SyncCursor(provider,resource,1,None,False)
        data=json.loads(self.path.read_text(encoding='utf-8')); item=data.get(f'{provider}:{resource}')
        if item is None: return SyncCursor(provider,resource,1,None,False)
        return SyncCursor(provider,resource,int(item['page']),item.get('updated_since'),bool(item.get('completed',False)))
    def save(self,cursor):
        data=json.loads(self.path.read_text(encoding='utf-8')) if self.path.exists() else {}
        data[f'{cursor.provider}:{cursor.resource}']={'page':cursor.page,'updated_since':cursor.updated_since,'completed':cursor.completed}
        self.path.parent.mkdir(parents=True,exist_ok=True); tmp=self.path.with_suffix(self.path.suffix+'.tmp')
        tmp.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8'); tmp.replace(self.path)
