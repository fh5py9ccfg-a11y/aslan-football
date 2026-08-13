from __future__ import annotations

from dataclasses import dataclass
import json


@dataclass(frozen=True)
class CertificateConfig:
    name: str
    namespace: str
    secret_name: str
    dns_names: tuple[str, ...]
    issuer_name: str


class CertificateRenderer:
    def render(self, config: CertificateConfig) -> str:
        if not config.dns_names:
            raise ValueError("En az bir DNS adı gereklidir")
        if not all([
            config.name.strip(),
            config.namespace.strip(),
            config.secret_name.strip(),
            config.issuer_name.strip(),
        ]):
            raise ValueError("Certificate alanları boş olamaz")

        for dns_name in config.dns_names:
            if "." not in dns_name:
                raise ValueError("Geçersiz DNS adı")

        return json.dumps(
            {
                "apiVersion": "cert-manager.io/v1",
                "kind": "Certificate",
                "metadata": {
                    "name": config.name,
                    "namespace": config.namespace,
                },
                "spec": {
                    "secretName": config.secret_name,
                    "dnsNames": list(config.dns_names),
                    "issuerRef": {
                        "name": config.issuer_name,
                        "kind": "ClusterIssuer",
                    },
                    "privateKey": {
                        "rotationPolicy": "Always",
                    },
                },
            },
            ensure_ascii=False,
            sort_keys=True,
        )
