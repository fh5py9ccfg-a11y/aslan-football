from dataclasses import asdict
from datetime import datetime, timezone
from uuid import uuid4
from aslan_ozaslan.engine import PredictionEngine
from aslan_ozaslan.storage.audit import AuditEvent, SQLiteAuditRepository

class AnalysisPipeline:
    def __init__(self, *, provider, engine: PredictionEngine, audit_repository: SQLiteAuditRepository):
        self.provider = provider
        self.engine = engine
        self.audit_repository = audit_repository

    def analyze(self, fixture_id: str):
        calculation_id = str(uuid4())
        match = self.provider.fetch_match(fixture_id)
        result = self.engine.predict(match)
        self.audit_repository.append(
            AuditEvent.create(
                event_type="prediction_calculated",
                fixture_id=fixture_id,
                status=result.status,
                model_version=result.model_version,
                calculation_id=calculation_id,
                payload={
                    "provider": self.provider.name,
                    "match": asdict(match),
                    "result": asdict(result),
                    "calculated_at": datetime.now(timezone.utc).isoformat(),
                    "cache_key": self.engine.cache_key(match, result.model_version),
                },
            )
        )
        return result
