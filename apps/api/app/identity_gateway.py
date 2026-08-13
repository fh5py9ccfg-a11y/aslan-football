from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class UnifiedPrincipal:
    subject: str
    roles: tuple[str, ...]
    token_id: str
    expires_at: int
    provider: str

class IdentityGateway:
    def __init__(
        self,
        *,
        local_service,
        oidc_verifier=None,
    ):
        self.local_service = local_service
        self.oidc_verifier = oidc_verifier

    def verify(self, token: str) -> UnifiedPrincipal:
        local_error = None
        try:
            principal = self.local_service.verify_access_token(
                token
            )
            return UnifiedPrincipal(
                subject=principal.subject,
                roles=principal.roles,
                token_id=principal.token_id,
                expires_at=principal.expires_at,
                provider="local",
            )
        except ValueError as exc:
            local_error = exc

        if self.oidc_verifier is None:
            raise ValueError(str(local_error))

        principal = self.oidc_verifier.verify(token)
        return UnifiedPrincipal(
            subject=principal.subject,
            roles=principal.roles,
            token_id=principal.token_id,
            expires_at=principal.expires_at,
            provider="oidc",
        )
