from __future__ import annotations

from dataclasses import dataclass
import json

from .cluster_manifest import ClusterManifest


@dataclass(frozen=True)
class KubernetesBundle:
    namespace_json: str
    deployments_json: tuple[str, ...]
    services_json: tuple[str, ...]


class KubernetesManifestRenderer:
    def render(self, manifest: ClusterManifest) -> KubernetesBundle:
        namespace_doc = {
            "apiVersion": "v1",
            "kind": "Namespace",
            "metadata": {"name": manifest.namespace},
        }

        deployments = []
        services = []

        for service in manifest.services:
            deployments.append(
                json.dumps(
                    {
                        "apiVersion": "apps/v1",
                        "kind": "Deployment",
                        "metadata": {
                            "name": service.name,
                            "namespace": manifest.namespace,
                        },
                        "spec": {
                            "replicas": service.replicas,
                            "selector": {"matchLabels": {"app": service.name}},
                            "template": {
                                "metadata": {"labels": {"app": service.name}},
                                "spec": {
                                    "containers": [
                                        {
                                            "name": service.name,
                                            "image": service.image,
                                            "ports": [{"containerPort": service.port}],
                                            "readinessProbe": {
                                                "httpGet": {
                                                    "path": service.readiness_path,
                                                    "port": service.port,
                                                }
                                            },
                                            "livenessProbe": {
                                                "httpGet": {
                                                    "path": service.liveness_path,
                                                    "port": service.port,
                                                }
                                            },
                                            "securityContext": {
                                                "readOnlyRootFilesystem": True,
                                                "runAsNonRoot": True,
                                                "allowPrivilegeEscalation": False,
                                            },
                                        }
                                    ]
                                },
                            },
                        },
                    },
                    ensure_ascii=False,
                    sort_keys=True,
                )
            )
            services.append(
                json.dumps(
                    {
                        "apiVersion": "v1",
                        "kind": "Service",
                        "metadata": {
                            "name": service.name,
                            "namespace": manifest.namespace,
                        },
                        "spec": {
                            "selector": {"app": service.name},
                            "ports": [
                                {
                                    "port": service.port,
                                    "targetPort": service.port,
                                }
                            ],
                        },
                    },
                    ensure_ascii=False,
                    sort_keys=True,
                )
            )

        return KubernetesBundle(
            namespace_json=json.dumps(namespace_doc, ensure_ascii=False, sort_keys=True),
            deployments_json=tuple(deployments),
            services_json=tuple(services),
        )
