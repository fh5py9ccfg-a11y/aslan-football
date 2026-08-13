from dataclasses import dataclass
from typing import Protocol
@dataclass(frozen=True)
class BrokerMessage:
    topic:str; partition:int; offset:int; key:str; value:dict; headers:dict[str,str]
class BrokerConsumer(Protocol):
    def poll(self,max_messages:int=100)->tuple[BrokerMessage,...]:...
    def commit(self,message:BrokerMessage)->None:...
class BrokerProducer(Protocol):
    def publish(self,*,topic:str,key:str,value:dict,headers:dict[str,str]|None=None)->None:...
