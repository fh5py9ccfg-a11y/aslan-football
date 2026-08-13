from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ControlCenterSnapshot:
    health_ok: bool
    audit_chain_ok: bool
    certificate_alerts: int
    dead_letter_jobs: int
    drift_alerts: int
    release_approved: bool
    release_ready: bool


class ControlCenterBuilder:
    def build(
        self,
        *,
        health_ok: bool,
        audit_chain_ok: bool,
        certificate_alerts: int,
        dead_letter_jobs: int,
        drift_alerts: int,
        release_approved: bool,
        policy_allowed: bool,
        signed_bundle_valid: bool,
    ) -> ControlCenterSnapshot:
        for value in (
            certificate_alerts,
            dead_letter_jobs,
            drift_alerts,
        ):
            if value < 0:
                raise ValueError("Kontrol merkezi sayaçları negatif olamaz")

        release_ready = all(
            [
                health_ok,
                audit_chain_ok,
                release_approved,
                policy_allowed,
                signed_bundle_valid,
                certificate_alerts == 0,
                dead_letter_jobs == 0,
            ]
        )

        return ControlCenterSnapshot(
            health_ok=health_ok,
            audit_chain_ok=audit_chain_ok,
            certificate_alerts=certificate_alerts,
            dead_letter_jobs=dead_letter_jobs,
            drift_alerts=drift_alerts,
            release_approved=release_approved,
            release_ready=release_ready,
        )
