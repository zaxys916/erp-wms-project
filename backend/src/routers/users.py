from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.database import get_db
from src.dependencies import require_permission
from src.models import User
from src.schemas import UserCreate, UserOut
from src.security import get_password_hash

router = APIRouter()

# 允许通过接口创建的角色（admin 只能由既有管理员手动维护）
ALLOWED_ROLES = ("user", "operator")


@router.post("/users", response_model=UserOut)
def create_user(
    user: UserCreate,
    db: Session = Depends(get_db),
    _: None = Depends(require_permission("user:manage")),
):
    """创建新用户（仅管理员；角色仅限 user/operator）"""
    if user.role not in ALLOWED_ROLES:
        raise HTTPException(status_code=400, detail="角色仅支持 user / operator")

    exists = (
        db.query(User)
        .filter((User.username == user.username) | (User.email == user.email))
        .first()
    )
    if exists:
        raise HTTPException(status_code=400, detail="用户名或邮箱已存在")

    new_user = User(
        username=user.username,
        email=user.email,
        role=user.role,
        password_hash=get_password_hash(user.password),
        is_active=True,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@router.get("/users", response_model=List[UserOut])
def get_all_users(
    db: Session = Depends(get_db),
    _: None = Depends(require_permission("user:manage")),
):
    """获取所有用户（仅管理员）"""
    return db.query(User).all()


@router.get("/users/{id}", response_model=UserOut)
def get_user(
    id: int,
    db: Session = Depends(get_db),
    _: None = Depends(require_permission("user:manage")),
):
    """获取单个用户（仅管理员）"""
    user = db.query(User).filter(User.id == id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.put("/users/{id}/enable", response_model=UserOut)
def enable_user(
    id: int,
    db: Session = Depends(get_db),
    _: None = Depends(require_permission("user:manage")),
):
    """启用用户（仅管理员）"""
    user = db.query(User).filter(User.id == id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_active = True
    db.commit()
    db.refresh(user)
    return user


@router.put("/users/{id}/disable", response_model=UserOut)
def disable_user(
    id: int,
    db: Session = Depends(get_db),
    _: None = Depends(require_permission("user:manage")),
):
    """禁用用户（仅管理员）"""
    user = db.query(User).filter(User.id == id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_active = False
    db.commit()
    db.refresh(user)
    return user


@router.put("/users/{id}/password")
def update_password(
    id: int,
    new_password: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("user:manage")),
):
    """重置用户密码（仅管理员；普通用户改密暂走此通道）"""
    user = db.query(User).filter(User.id == id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.password_hash = get_password_hash(new_password)
    db.commit()
    return {"message": "Password updated successfully"}
