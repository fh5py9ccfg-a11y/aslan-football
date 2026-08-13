class KafkaAdapterUnavailable(RuntimeError):pass
class KafkaConsumerAdapter:
    def __init__(self,*a,**k):
        try: import confluent_kafka
        except ImportError as e: raise KafkaAdapterUnavailable('confluent-kafka ve broker yapılandırması gerekli') from e
        raise NotImplementedError('bootstrap server, TLS/SASL, topic ve consumer group gerekli')
class KafkaProducerAdapter(KafkaConsumerAdapter):pass
