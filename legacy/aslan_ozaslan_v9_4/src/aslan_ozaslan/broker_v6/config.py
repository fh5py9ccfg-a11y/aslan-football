from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class KafkaConnectionConfig:
    bootstrap_servers: tuple[str, ...]
    client_id: str
    consumer_group: str
    security_protocol: str = "PLAINTEXT"
    sasl_mechanism: str | None = None

    def validate(self) -> None:
        if not self.bootstrap_servers:
            raise ValueError("En az bir bootstrap server gerekir")
        if any(not item.strip() for item in self.bootstrap_servers):
            raise ValueError("Bootstrap server boş olamaz")
        if not self.client_id.strip() or not self.consumer_group.strip():
            raise ValueError("client_id ve consumer_group zorunludur")
        if self.security_protocol not in {
            "PLAINTEXT", "SSL", "SASL_PLAINTEXT", "SASL_SSL"
        }:
            raise ValueError("Geçersiz security_protocol")
        if self.security_protocol.startswith("SASL") and not self.sasl_mechanism:
            raise ValueError("SASL için sasl_mechanism gerekir")
