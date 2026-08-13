from __future__ import annotations

from dataclasses import dataclass
import json


@dataclass(frozen=True)
class ExternalSecretRef:
    secret_key: str
    remote_key: str
    property_name: str


@dataclass(frozen=True)
class ExternalSecretConfig:
    name: str
    namespace: str
    secret_store_name: str
    target_secret_name: str
    refresh_interval: str
    refs: tuple[ExternalSecretRef, ...]


class ExternalSecretRenderer:
    def render(self, config: ExternalSecretConfig) -> str:
        if not config.refs:
            raise ValueError("En az bir external secret referansı gereklidir")
        if not all([
            config.name.strip(),
            config.namespace.strip(),
            config.secret_store_name.strip(),
            config.target_secret_name.strip(),
            config.refresh_interval.strip(),
        ]):
            raise ValueError("External secret alanları boş olamaz")

        return json.dumps(
            {
                "apiVersion": "external-secrets.io/v1beta1",
                "kind": "ExternalSecret",
                "metadata": {
                    "name": config.name,
                    "namespace": config.namespace,
                },
                "spec": {
                    "refreshInterval": config.refresh_interval,
                    "secretStoreRef": {
                        "name": config.secret_store_name,
                        "kind": "ClusterSecretStore",
                    },
                    "target": {
                        "name": config.target_secret_name,
                        "creationPolicy": "Owner",
                    },
                    "data": [
                        {
                            "secretKey": ref.secret_key,
                            "remoteRef": {
                                "key": ref.remote_key,
                                "property": ref.property_name,
                            },
                        }
                        for ref in config.refs
                    ],
                },
            },
            ensure_ascii=False,
            sort_keys=True,
        )
