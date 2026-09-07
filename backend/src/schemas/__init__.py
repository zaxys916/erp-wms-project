"""Pydantic 数据校验模型（请求体 / 响应体）。

同时从 src.models 重新导出 ORM 实体，方便路由层使用
`from src.schemas import WarehouseCreate, Warehouse` 一次导入。
"""
from datetime import datetime
from typing import Generic, List, Optional, TypeVar

from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.models import (  # noqa: F401  重新导出 ORM 实体
    Discrepancy,
    Inventory,
    InventoryMovement,
    Product,
    StockOrder,
    Stocktaking,
    StocktakingItem,
    User,
    Warehouse,
    Zone,
)

__all__ = [
    "Page",
    "WarehouseCreate",
    "WarehouseOut",
    "ProductCreate",
    "ProductOut",
    "ZoneCreate",
    "ZoneOut",
    "UserCreate",
    "UserOut",
    "InventoryCreate",
    "InventoryOut",
    "StockOrderCreate",
    "StockOrderOut",
    "InventoryMovementOut",
    "StocktakingCreate",
    "StocktakingOut",
    "StocktakingItemOut",
    "StocktakingItemUpdate",
    "StocktakingDetail",
    "DiscrepancyOut",
    # 重新导出的 ORM 实体
    "User",
    "Warehouse",
    "Product",
    "Zone",
    "Inventory",
    "StockOrder",
    "InventoryMovement",
    "Stocktaking",
    "StocktakingItem",
    "Discrepancy",
]


class ORMModel(BaseModel):
    """通用响应模型：允许从 SQLAlchemy 实例直接序列化。"""

    model_config = ConfigDict(from_attributes=True)


# 分页结果：所有列表接口统一返回 {items, total, page, page_size}
T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    page_size: int


# ---------- Warehouse ----------
class WarehouseCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    location: Optional[str] = None


class WarehouseOut(ORMModel):
    id: int
    name: str
    location: Optional[str] = None
    created_at: Optional[datetime] = None


# ---------- Product ----------
class ProductCreate(BaseModel):
    name: str = Field(..., min_length=3)
    sku: str = Field(..., pattern=r"^[A-Z0-9]{8}$")


class ProductOut(ORMModel):
    id: int
    name: str
    sku: Optional[str] = None
    created_at: Optional[datetime] = None


# ---------- Zone ----------
class ZoneCreate(BaseModel):
    zone_name: str = Field(..., min_length=1, max_length=100)
    capacity: int = Field(..., ge=0)
    status: bool = True
    warehouse_id: Optional[int] = None


class ZoneOut(ORMModel):
    id: int
    zone_name: str
    capacity: int
    status: bool
    warehouse_id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# ---------- User ----------
class UserCreate(BaseModel):
    username: str = Field(..., min_length=1, max_length=20)
    email: str = Field(..., max_length=120, description="邮箱，需包含有效域名")
    password: str = Field(..., min_length=1, description="明文密码，服务端哈希后存储")
    role: str = "user"

    @field_validator("email")
    @classmethod
    def _check_email(cls, v: str) -> str:
        value = v.strip().lower()
        if "@" not in value or "." not in value.rsplit("@", 1)[-1]:
            raise ValueError("邮箱格式不正确")
        return value


class UserOut(ORMModel):
    id: int
    username: Optional[str] = None
    email: Optional[str] = None
    is_active: Optional[bool] = None
    role: Optional[str] = None
    created_at: Optional[datetime] = None


# ---------- Inventory ----------
class InventoryCreate(BaseModel):
    product_id: int
    zone_id: int
    quantity: int = Field(default=0, ge=0)


class InventoryOut(ORMModel):
    id: int
    product_id: int
    zone_id: int
    quantity: int
    last_updated: Optional[datetime] = None


# ---------- 出入库单据 StockOrder ----------
class StockOrderCreate(BaseModel):
    order_type: str = Field(..., pattern="^(in|out)$", description="单据类型：in=入库，out=出库")
    product_id: int
    zone_id: int
    quantity: int = Field(..., ge=1)
    remark: Optional[str] = None


class StockOrderOut(ORMModel):
    id: int
    order_no: str
    order_type: str
    product_id: int
    zone_id: int
    quantity: int
    status: str  # pending / approved / rejected / cancelled
    remark: Optional[str] = None
    created_by: Optional[int] = None
    approved_by: Optional[int] = None
    created_at: Optional[datetime] = None
    approved_at: Optional[datetime] = None


# ---------- 库存流水 InventoryMovement ----------
class InventoryMovementOut(ORMModel):
    id: int
    product_id: int
    zone_id: int
    movement_type: str  # in / out / adjust
    quantity: int
    balance_after: int
    ref_no: Optional[str] = None
    remark: Optional[str] = None
    created_by: Optional[int] = None
    created_at: Optional[datetime] = None


# ---------- 盘点 Stocktaking ----------
class StocktakingCreate(BaseModel):
    zone_id: Optional[int] = Field(default=None, description="盘点库位；为空表示全仓盘点")
    remark: Optional[str] = None


class StocktakingOut(ORMModel):
    id: int
    order_no: str
    zone_id: Optional[int] = None
    status: str  # pending / completed
    remark: Optional[str] = None
    created_by: Optional[int] = None
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class StocktakingItemOut(ORMModel):
    id: int
    stocktaking_id: int
    product_id: int
    zone_id: int
    book_qty: int
    actual_qty: Optional[int] = None
    diff: int


class StocktakingItemUpdate(BaseModel):
    actual_qty: int = Field(..., ge=0)


class StocktakingDetail(StocktakingOut):
    items: List[StocktakingItemOut] = []


# ---------- 盘点差异 Discrepancy ----------
class DiscrepancyOut(ORMModel):
    id: int
    stocktaking_id: Optional[int] = None
    product_id: int
    zone_id: Optional[int] = None
    book_qty: int
    actual_qty: int
    difference: int
    status: str  # open / adjusted
    handled_by: Optional[int] = None
    created_at: Optional[datetime] = None
