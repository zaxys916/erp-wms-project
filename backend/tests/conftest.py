"""pytest 全局配置。

测试策略：使用内存 SQLite + StaticPool，并通过 dependency_overrides 把
src.database.get_db 替换为测试会话，从而完全隔离 MySQL 生产库，
本地与 CI 均可直接运行，无需启动 MySQL 服务。
"""
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# 保证能 import src.*（以 backend 目录为根）
BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from src.base import Base  # noqa: E402
from src.database import get_db  # noqa: E402
from src.main import app  # noqa: E402
from src.models import User  # noqa: E402
from src.security import get_password_hash  # noqa: E402

# 内存 SQLite：单连接共享，保证多个 session 看到同一份数据
engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def _create_schema():
    """整个测试会话只建一次表。"""
    Base.metadata.create_all(engine)
    yield


@pytest.fixture(autouse=True)
def _clean_tables():
    """每个用例结束后清空所有表，保证用例相互独立。"""
    yield
    with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(table.delete())


@pytest.fixture()
def client():
    """提供 TestClient，并将每个请求的 DB 会话替换为测试库会话。"""

    def override_get_db():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db

    # 预置管理员账号（bcrypt 哈希）
    with TestingSessionLocal() as session:
        admin = session.query(User).filter(User.username == "admin").first()
        if admin is None:
            session.add(
                User(
                    username="admin",
                    email="admin@wms.dev",
                    role="admin",
                    password_hash=get_password_hash("admin123"),
                    is_active=True,
                )
            )
            session.commit()

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
