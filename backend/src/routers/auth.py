"""认证路由：登录签发 JWT、注册、获取当前用户。"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from src.database import get_db
from src.dependencies import get_current_active_user
from src.models import User
from src.schemas import UserCreate, UserOut
from src.security import create_access_token, get_password_hash, verify_password

router = APIRouter()


@router.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """用户登录，返回 access_token。"""
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="用户已被禁用")

    return {
        "access_token": create_access_token(data={"sub": user.username}),
        "token_type": "bearer",
    }


@router.post("/register", response_model=UserOut)
def register(user: UserCreate, db: Session = Depends(get_db)):
    """注册新用户（统一注册为普通 user 角色，防越权）"""
    exists = (
        db.query(User)
        .filter((User.username == user.username) | (User.email == user.email))
        .first()
    )
    if exists:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="用户名或邮箱已存在")

    new_user = User(
        username=user.username,
        email=user.email,
        role="user",
        password_hash=get_password_hash(user.password),
        is_active=True,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@router.get("/users/me", response_model=UserOut)
def read_me(current_user: User = Depends(get_current_active_user)):
    """获取当前登录用户信息。"""
    return current_user


@router.post("/logout")
def logout():
    """登出（前端清除本地 token 即可）。"""
    return {"message": "Logged out successfully"}
