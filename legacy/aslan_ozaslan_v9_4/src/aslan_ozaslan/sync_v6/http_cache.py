from dataclasses import dataclass
@dataclass(frozen=True)
class CacheEntry:
    etag:str|None; last_modified:str|None; payload:dict|None
class ConditionalRequestCache:
    def __init__(self): self._entries={}
    def request_headers(self,key):
        e=self._entries.get(key); h={}
        if not e: return h
        if e.etag: h['If-None-Match']=e.etag
        if e.last_modified: h['If-Modified-Since']=e.last_modified
        return h
    def update(self,key,*,etag,last_modified,payload): self._entries[key]=CacheEntry(etag,last_modified,dict(payload))
    def resolve_not_modified(self,key):
        e=self._entries.get(key)
        if not e or e.payload is None: raise KeyError('304 yanıtı için cache kaydı bulunamadı')
        return dict(e.payload)
