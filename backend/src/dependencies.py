"""FastAPI 认证与授权依赖。"""
from typing import List, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from src.database import get_db
from src.models import User
from src.security import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token", auto_error=False)

# 角色 -> 权限列表；admin 拥有全部权限（"*"）
ROLE_PERMISSIONS = {
    "admin": ["*"],
    "operator": [
        "warehouse:read",
        "zone:read",
        "zone:write",
        "product:read",
        "product:write",
        "inventory:read",
        "inventory:write",
        "movement:read",
        "stocktake:read",
        "stocktake:write",
        "supplier:read",
        "supplier:write",
        "customer:read",
        "customer:write",
        "purchase:read",
        "purchase:write",
        "sale:read",
        "sale:write",
        "report:read",
        "alert:read",
    ],
    # 普通注册用户仅可浏览
    "user": [
        "warehouse:read",
        "zone:read",
        "product:read",
        "inventory:read",
        "movement:read",
        "stocktake:read",
        "supplier:read",
        "customer:read",
        "purchase:read",
        "sale:read",
        "report:read",
        "alert:read",
    ],
}


def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """从 Bearer Token 解析当前用户。"""
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise credentials_exc

    payload = decode_access_token(token)
    if not payload or not payload.get("sub"):
        raise credentials_exc

    user = db.query(User).filter(User.username == payload["sub"]).first()
    if user is None:
        raise credentials_exc
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="用户已被禁用")
    return user


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """校验当前用户处于激活状态。"""
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")
    return current_user


def user_permissions(role: str) -> List[str]:
    return ROLE_PERMISSIONS.get(role, [])


def require_permission(permission: str):
    """权限校验依赖工厂。"""

    def _checker(current_user: User = Depends(get_current_active_user)) -> User:
        perms = user_permissions(current_user.role or "user")
        if "*" in perms or permission in perms:
            return current_user
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"您没有足够的权限: {permission}",
        )

    return _checker
