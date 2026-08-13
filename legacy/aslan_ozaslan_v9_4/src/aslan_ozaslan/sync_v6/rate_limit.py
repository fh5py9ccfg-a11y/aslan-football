import time
from dataclasses import dataclass
@dataclass(frozen=True)
class RateLimitDecision:
    allowed:bool; wait_seconds:float; remaining:int
class RateLimitManager:
    def __init__(self,*,capacity:int,refill_per_second:float):
        if capacity<=0 or refill_per_second<=0: raise ValueError('Rate limit değerleri pozitif olmalıdır')
        self.capacity=capacity; self.refill_per_second=refill_per_second; self.tokens=float(capacity); self.last_refill=time.monotonic()
    def acquire(self,cost:int=1):
        if cost<=0: raise ValueError('cost pozitif olmalıdır')
        now=time.monotonic(); elapsed=max(0.0,now-self.last_refill)
        self.tokens=min(float(self.capacity),self.tokens+elapsed*self.refill_per_second); self.last_refill=now
        if self.tokens>=cost:
            self.tokens-=cost; return RateLimitDecision(True,0.0,int(self.tokens))
        return RateLimitDecision(False,(cost-self.tokens)/self.refill_per_second,int(self.tokens))
