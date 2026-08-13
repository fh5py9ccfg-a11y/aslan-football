from dataclasses import dataclass
from datetime import datetime,timedelta,timezone
from typing import Protocol,Any
class CacheAdapter(Protocol):
    def get(self,key:str)->Any|None: ...
    def set(self,key:str,value:Any,ttl_seconds:int)->None: ...
    def delete(self,key:str)->None: ...
@dataclass
class CacheEntry:
    value: Any
    expires_at: datetime
class MemoryCache:
    def __init__(self): self._entries={}
    def get(self,key):
        entry=self._entries.get(key)
        if entry is None: return None
        if datetime.now(timezone.utc)>=entry.expires_at:
            self._entries.pop(key,None); return None
        return entry.value
    def set(self,key,value,ttl_seconds):
        if ttl_seconds<=0: raise ValueError('TTL pozitif olmalıdır')
        self._entries[key]=CacheEntry(value,datetime.now(timezone.utc)+timedelta(seconds=ttl_seconds))
    def delete(self,key): self._entries.pop(key,None)
