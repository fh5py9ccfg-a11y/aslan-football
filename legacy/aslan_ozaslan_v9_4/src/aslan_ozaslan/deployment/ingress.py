from __future__ import annotations

from dataclasses import dataclass
import json


@dataclass(frozen=True)
class IngressConfig:
    namespace: str
    host: str
    service_name: str
    service_port: int
    tls_secret_name: str


class IngressRenderer:
    def render(self, config: IngressConfig) -> str:
        if not config.host.strip() or "." not in config.host:
            raise ValueError("Geçerli host gerekli")
        if not config.tls_secret_name.strip():
            raise ValueError("TLS secret gerekli")
        if not 1 <= config.service_port <= 65535:
            raise ValueError("Geçersiz servis portu")

        return json.dumps(
            {
                "apiVersion": "networking.k8s.io/v1",
                "kind": "Ingress",
                "metadata": {
                    "name": f"{config.service_name}-ingress",
                    "namespace": config.namespace,
                    "annotations": {
                        "nginx.ingress.kubernetes.io/ssl-redirect": "true",
                    },
                },
                "spec": {
                    "tls": [
                        {
                            "hosts": [config.host],
                            "secretName": config.tls_secret_name,
                        }
                    ],
                    "rules": [
                        {
                            "host": config.host,
                            "http": {
                                "paths": [
                                    {
                                        "path": "/",
                                        "pathType": "Prefix",
                                        "backend": {
                                            "service": {
                                                "name": config.service_name,
                                                "port": {
                                                    "number": config.service_port
                                                },
                                            }
                                        },
                                    }
                                ]
                            },
                        }
                    ],
                },
            },
            ensure_ascii=False,
            sort_keys=True,
        )
