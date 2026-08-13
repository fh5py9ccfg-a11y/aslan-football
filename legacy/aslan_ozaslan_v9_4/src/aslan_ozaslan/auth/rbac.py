from __future__ import annotations

from enum import Enum


class Permission(str, Enum):
    VIEW_ANALYSIS = "VIEW_ANALYSIS"
    RUN_ANALYSIS = "RUN_ANALYSIS"
    MANAGE_DATA = "MANAGE_DATA"
    MANAGE_USERS = "MANAGE_USERS"
    DEPLOY_MODEL = "DEPLOY_MODEL"


class RoleAuthorizer:
    ROLE_PERMISSIONS = {
        "OWNER": set(Permission),
        "ADMIN": {
            Permission.VIEW_ANALYSIS,
            Permission.RUN_ANALYSIS,
            Permission.MANAGE_DATA,
            Permission.MANAGE_USERS,
        },
        "ANALYST": {
            Permission.VIEW_ANALYSIS,
            Permission.RUN_ANALYSIS,
        },
        "VIEWER": {
            Permission.VIEW_ANALYSIS,
        },
    }

    def is_allowed(self, role: str, permission: Permission) -> bool:
        return permission in self.ROLE_PERMISSIONS.get(role, set())

    def require(self, role: str, permission: Permission) -> None:
        if not self.is_allowed(role, permission):
            raise PermissionError(f"{role} rolü için izin yok: {permission.value}")
