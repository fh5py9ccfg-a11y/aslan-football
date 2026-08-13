from __future__ import annotations

from dataclasses import dataclass

from aslan_ozaslan.policy import PolicyEngine, PolicyRule


@dataclass(frozen=True)
class DeploymentPolicyContext:
    production: bool
    replicas: int
    image_reference: str
    tls_enabled: bool
    external_secrets_enabled: bool
    network_policy_enabled: bool


class DeploymentPolicyBundle:
    def evaluate(self, context: DeploymentPolicyContext):
        values = {
            "production": context.production,
            "replicas": context.replicas,
            "image_reference": context.image_reference,
            "tls_enabled": context.tls_enabled,
            "external_secrets_enabled": context.external_secrets_enabled,
            "network_policy_enabled": context.network_policy_enabled,
        }

        rules = [
            PolicyRule(
                "immutable_image",
                "BLOCKER",
                lambda item: "@sha256:" in item["image_reference"],
                "image digest zorunlu",
            ),
            PolicyRule(
                "production_replicas",
                "BLOCKER",
                lambda item: (not item["production"]) or item["replicas"] >= 2,
                "production en az iki replica gerektirir",
            ),
            PolicyRule(
                "tls",
                "BLOCKER",
                lambda item: (not item["production"]) or item["tls_enabled"],
                "production TLS gerektirir",
            ),
            PolicyRule(
                "external_secrets",
                "BLOCKER",
                lambda item: (not item["production"]) or item["external_secrets_enabled"],
                "production external secrets gerektirir",
            ),
            PolicyRule(
                "network_policy",
                "WARNING",
                lambda item: item["network_policy_enabled"],
                "network policy önerilir",
            ),
        ]
        return PolicyEngine().evaluate(values, rules)
