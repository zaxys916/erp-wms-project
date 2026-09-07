from datetime import datetime

from sqlalchemy import Column, DateTime, Integer
from sqlalchemy.orm import declarative_base

# 全局唯一的 declarative_base，所有 ORM 模型与 schema 均引用此处
Base = declarative_base()


class BaseModel:
    """可复用的公共字段（id / created_at），供 ORM 模型继承。"""

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.now)

    def __repr__(self):
        return f"<{self.__class__.__name__}(id={self.id})>"


__all__ = ["Base", "BaseModel"]
