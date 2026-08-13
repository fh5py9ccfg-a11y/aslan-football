from __future__ import annotations

from dataclasses import dataclass

from aslan_ozaslan.auth import Permission, RoleAuthorizer


@dataclass(frozen=True)
class AdminRequestContext:
    session_token: str
    csrf_token: str | None
    method: str


class AdminRouteGuard:
    def __init__(self, session_store, csrf_manager, authorizer: RoleAuthorizer | None = None):
        self.session_store = session_store
        self.csrf_manager = csrf_manager
        self.authorizer = authorizer or RoleAuthorizer()

    def authorize(self, context: AdminRequestContext):
        session = self.session_store.validate(context.session_token)
        if session is None:
            raise PermissionError("unauthorized")

        self.authorizer.require(session.role, Permission.MANAGE_DATA)

        if context.method.upper() not in {"GET", "HEAD"}:
            if not context.csrf_token:
                raise PermissionError("csrf_required")
            if not self.csrf_manager.validate(context.session_token, context.csrf_token):
                raise PermissionError("csrf_failed")

        return session
