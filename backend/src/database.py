from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.base import Base
from src.config import DATABASE_URL

# MySQL 通过 PyMySQL 驱动连接，不需要 SQLite 的 check_same_thread 参数
engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
    pool_recycle=3600,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=True, bind=engine)


def get_db():
    """请求级数据库会话依赖。

    这里只做资源回收，不捕获业务异常——否则路由内抛出的
    HTTPException 会被统一转成 500，导致 401/403/404 等状态码丢失。
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


__all__ = ["Base", "engine", "SessionLocal", "get_db"]
