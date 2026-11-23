from fastapi import Depends, HTTPException, status

from app.api.dependencies import get_current_principal


def require_permission(permission: str):
    def dependency(principal: dict = Depends(get_current_principal)) -> dict:
        permissions = principal.get("permissions", [])
        if "*" not in permissions and permission not in permissions:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permission")
        return principal
    return dependency
