from functools import wraps
from fastapi import Depends, HTTPException, status
from app.api.v1.deps import get_current_user
from app.models.user import User

ROLE_PERMISSIONS: dict[str, list[str]] = {
    "admin": ["*"],
    "data_engineer": [
        "connection:read", "connection:write",
        "pipeline:read", "pipeline:write", "pipeline:run",
        "job:read", "log:read", "schedule:write",
        "rejected:read",
    ],
    "operator": [
        "connection:read",
        "pipeline:read", "pipeline:run",
        "job:read", "log:read", "rejected:read",
    ],
    "business_user": [
        "pipeline:read", "job:read", "log:read",
    ],
    "viewer": [
        "pipeline:read", "job:read", "log:read",
    ],
}


def has_permission(user: User, permission: str) -> bool:
    for role in user.roles:
        perms = ROLE_PERMISSIONS.get(role.name, [])
        if "*" in perms or permission in perms:
            return True
    return False


def require_permission(permission: str):
    """FastAPI dependency factory for permission checking."""
    async def _check(current_user: User = Depends(get_current_user)):
        if not has_permission(current_user, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {permission}",
            )
        return current_user
    return _check
