import hashlib, json
class IdempotencyStore:
    def __init__(self): self._records={}
    def fingerprint(self,operation,payload):
        canonical=json.dumps(payload,ensure_ascii=False,sort_keys=True,separators=(',',':'))
        return hashlib.sha256(f'{operation}:{canonical}'.encode()).hexdigest()
    def seen(self,key): return key in self._records
    def record(self,key,result):
        self._records[key]=hashlib.sha256(json.dumps(result,sort_keys=True,default=str).encode()).hexdigest()
        return self._records[key]
