from __future__ import annotations

from dataclasses import dataclass
import json


@dataclass(frozen=True)
class NetworkRule:
    from_app: str
    to_app: str
    port: int


class NetworkPolicyRenderer:
    def render_default_deny(self, namespace: str) -> str:
        if not namespace.strip():
            raise ValueError("Namespace boş olamaz")
        return json.dumps(
            {
                "apiVersion": "networking.k8s.io/v1",
                "kind": "NetworkPolicy",
                "metadata": {
                    "name": "default-deny",
                    "namespace": namespace,
                },
                "spec": {
                    "podSelector": {},
                    "policyTypes": ["Ingress", "Egress"],
                },
            },
            ensure_ascii=False,
            sort_keys=True,
        )

    def render_allow(self, namespace: str, rule: NetworkRule) -> str:
        if not 1 <= rule.port <= 65535:
            raise ValueError("Geçersiz port")
        return json.dumps(
            {
                "apiVersion": "networking.k8s.io/v1",
                "kind": "NetworkPolicy",
                "metadata": {
                    "name": f"allow-{rule.from_app}-to-{rule.to_app}",
                    "namespace": namespace,
                },
                "spec": {
                    "podSelector": {
                        "matchLabels": {"app": rule.to_app}
                    },
                    "policyTypes": ["Ingress"],
                    "ingress": [
                        {
                            "from": [
                                {
                                    "podSelector": {
                                        "matchLabels": {"app": rule.from_app}
                                    }
                                }
                            ],
                            "ports": [
                                {"protocol": "TCP", "port": rule.port}
                            ],
                        }
                    ],
                },
            },
            ensure_ascii=False,
            sort_keys=True,
        )
