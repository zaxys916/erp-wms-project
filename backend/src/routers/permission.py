"""权限控制路由：查询角色权限矩阵与当前用户权限。"""
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.dependencies import ROLE_PERMISSIONS, get_current_active_user, require_permission, user_permissions
from src.database import get_db
from src.models import User

router = APIRouter()


@router.get("/roles")
def list_roles():
    """返回所有角色及其权限。"""
    return {"roles": ROLE_PERMISSIONS}


@router.get("/me/permissions", response_model=List[str])
def my_permissions(current_user: User = Depends(get_current_active_user)):
    """返回当前登录用户拥有的权限列表。"""
    return user_permissions(current_user.role or "user")


@router.get("/users/{id}/roles")
def user_role(
    id: int,
    db: Session = Depends(get_db),
    _: None = Depends(require_permission("user:manage")),
):
    """查询指定用户的角色（仅管理员）"""
    user = db.query(User).filter(User.id == id).first()
    if not user:
        return {"id": id, "role": None}
    return {"id": user.id, "role": user.role, "permissions": user_permissions(user.role or "user")}
