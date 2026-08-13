from __future__ import annotations

from dataclasses import dataclass
import json


@dataclass(frozen=True)
class GatekeeperConstraint:
    name: str
    kind: str
    message: str
    parameters: dict


class GatekeeperRenderer:
    def render_template(self, *, name: str, rego: str) -> str:
        if not name.strip() or not rego.strip():
            raise ValueError("Template adı ve Rego içeriği boş olamaz")
        return json.dumps(
            {
                "apiVersion": "templates.gatekeeper.sh/v1",
                "kind": "ConstraintTemplate",
                "metadata": {"name": name},
                "spec": {
                    "crd": {
                        "spec": {
                            "names": {"kind": name}
                        }
                    },
                    "targets": [
                        {
                            "target": "admission.k8s.gatekeeper.sh",
                            "rego": rego,
                        }
                    ],
                },
            },
            ensure_ascii=False,
            sort_keys=True,
        )

    def render_constraint(self, constraint: GatekeeperConstraint) -> str:
        if not constraint.name.strip() or not constraint.kind.strip():
            raise ValueError("Constraint adı ve türü boş olamaz")
        return json.dumps(
            {
                "apiVersion": "constraints.gatekeeper.sh/v1beta1",
                "kind": constraint.kind,
                "metadata": {"name": constraint.name},
                "spec": {
                    "match": {
                        "kinds": [
                            {
                                "apiGroups": ["apps"],
                                "kinds": ["Deployment"],
                            }
                        ]
                    },
                    "parameters": dict(constraint.parameters),
                    "enforcementAction": "deny",
                },
            },
            ensure_ascii=False,
            sort_keys=True,
        )


def immutable_image_rego() -> str:
    return '''
package k8simmutableimage

violation[{"msg": msg}] {
  container := input.review.object.spec.template.spec.containers[_]
  not contains(container.image, "@sha256:")
  msg := sprintf("image digest ile sabitlenmeli: %v", [container.image])
}
'''.strip()
