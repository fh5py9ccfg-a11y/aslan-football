from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json


@dataclass(frozen=True)
class SoftwareComponent:
    name: str
    version: str
    license: str
    source: str
    sha256: str


class SbomBuilder:
    def build(
        self,
        *,
        document_name: str,
        version: str,
        components: tuple[SoftwareComponent, ...],
    ) -> dict:
        payload = {
            "bomFormat": "CycloneDX",
            "specVersion": "1.5",
            "version": 1,
            "metadata": {
                "component": {
                    "type": "application",
                    "name": document_name,
                    "version": version,
                }
            },
            "components": [
                {
                    "type": "library",
                    "name": item.name,
                    "version": item.version,
                    "licenses": [
                        {
                            "license": {
                                "name": item.license
                            }
                        }
                    ],
                    "externalReferences": [
                        {
                            "type": "distribution",
                            "url": item.source,
                        }
                    ],
                    "hashes": [
                        {
                            "alg": "SHA-256",
                            "content": item.sha256,
                        }
                    ],
                }
                for item in components
            ],
        }
        canonical = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return {
            **payload,
            "documentSha256": hashlib.sha256(
                canonical
            ).hexdigest(),
        }
