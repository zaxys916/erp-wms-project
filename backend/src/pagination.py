"""分页工具：对 SQLAlchemy Query 统一执行 count + offset/limit。"""
from typing import Any, Dict

from sqlalchemy.orm import Query


def paginate(query: Query, page: int, page_size: int) -> Dict[str, Any]:
    """执行分页并返回统一结构 {items, total, page, page_size}。

    page/page_size 均已由 FastAPI Query 参数保证 >=1。
    """
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return {"items": items, "total": total, "page": page, "page_size": page_size}
