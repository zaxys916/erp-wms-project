from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)

from src.base import Base

__all__ = [
    "Base",
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
    "Supplier",
    "Customer",
    "PurchaseOrder",
    "PurchaseOrderItem",
    "SalesOrder",
    "SalesOrderItem",
]


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(20), unique=True, index=True)
    email = Column(String(120), unique=True, index=True)
    password_hash = Column(String(255))
    is_active = Column(Boolean, default=True)
    role = Column(String(20), default="user")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, onupdate=datetime.now)


class Warehouse(Base):
    __tablename__ = "warehouses"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    location = Column(String(200))
    created_at = Column(DateTime, default=datetime.now)


class Product(Base):
    """产品：库存数量以 inventory 台账聚合为准，不再在 products 冗余 quantity 字段。"""

    __tablename__ = "products"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    sku = Column(String(50), unique=True)
    # 业务扩展字段（阶段三）：安全库存阈值、销售价、成本价（用于报表与预警）
    safety_stock = Column(Integer, nullable=False, default=0)
    price = Column(Numeric(12, 2), nullable=False, default=0)
    cost = Column(Numeric(12, 2), nullable=False, default=0)
    created_at = Column(DateTime, default=datetime.now)


class Zone(Base):
    """库位：归属于某个仓库，记录容量与启用状态。"""

    __tablename__ = "zones"
    __table_args__ = (UniqueConstraint("warehouse_id", "zone_name", name="uq_zone_warehouse_name"),)

    id = Column(Integer, primary_key=True)
    zone_name = Column(String(100), nullable=False)
    capacity = Column(Integer, nullable=False, default=0)
    status = Column(Boolean, default=True)  # True=启用
    warehouse_id = Column(Integer, ForeignKey("warehouses.id"))
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, onupdate=datetime.now)


class Inventory(Base):
    """库存：某产品在某个库位上的实际数量。"""

    __tablename__ = "inventory"
    __table_args__ = (UniqueConstraint("product_id", "zone_id", name="uq_inventory_product_zone"),)

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    zone_id = Column(Integer, ForeignKey("zones.id"), nullable=False)
    quantity = Column(Integer, nullable=False, default=0)
    last_updated = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class StockOrder(Base):
    """出入库单据：入库单(in)/出库单(out)，审核后更新库存。"""

    __tablename__ = "stock_orders"

    id = Column(Integer, primary_key=True)
    order_no = Column(String(30), unique=True, index=True, nullable=False)
    order_type = Column(String(10), nullable=False)  # in / out
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    zone_id = Column(Integer, ForeignKey("zones.id"), nullable=False, index=True)
    quantity = Column(Integer, nullable=False, default=0)
    status = Column(String(20), default="pending")  # pending / approved / rejected / cancelled
    remark = Column(String(255))
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.now, index=True)
    approved_at = Column(DateTime)


class InventoryMovement(Base):
    """库存流水：每一次库存变动都记录，支持追溯。"""

    __tablename__ = "inventory_movement"

    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    zone_id = Column(Integer, ForeignKey("zones.id"), nullable=False, index=True)
    movement_type = Column(String(10), nullable=False)  # in / out / adjust
    quantity = Column(Integer, nullable=False, default=0)
    balance_after = Column(Integer, nullable=False, default=0)
    ref_no = Column(String(50))  # 关联单据号/盘点单号
    remark = Column(String(255))
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.now, index=True)


class Stocktaking(Base):
    """盘点单：冻结某库位当前库存快照，记录实际盘点结果。"""

    __tablename__ = "stocktaking"

    id = Column(Integer, primary_key=True)
    order_no = Column(String(30), unique=True, index=True, nullable=False)
    zone_id = Column(Integer, ForeignKey("zones.id"), nullable=True, index=True)
    status = Column(String(20), default="pending")  # pending / completed
    remark = Column(String(255))
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    completed_at = Column(DateTime)


class StocktakingItem(Base):
    """盘点明细：账面数量(book_qty) vs 实际数量(actual_qty)。

    zone_id 记录该产品在哪个库位上被盘点，支持按库位或全仓盘点。
    """

    __tablename__ = "stocktaking_item"
    __table_args__ = (
        UniqueConstraint("stocktaking_id", "product_id", "zone_id", name="uq_stocktaking_item"),
    )

    id = Column(Integer, primary_key=True)
    stocktaking_id = Column(Integer, ForeignKey("stocktaking.id"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    zone_id = Column(Integer, ForeignKey("zones.id"), nullable=False)
    book_qty = Column(Integer, nullable=False, default=0)
    actual_qty = Column(Integer, nullable=True)
    diff = Column(Integer, nullable=False, default=0)  # actual - book


class Discrepancy(Base):
    """盘点差异报告：盘点完成后差异非零的明细自动生成。"""

    __tablename__ = "discrepancies"

    id = Column(Integer, primary_key=True)
    stocktaking_id = Column(Integer, ForeignKey("stocktaking.id"), nullable=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    zone_id = Column(Integer, ForeignKey("zones.id"), nullable=True, index=True)
    book_qty = Column(Integer, nullable=False, default=0)
    actual_qty = Column(Integer, nullable=False, default=0)
    difference = Column(Integer, nullable=False, default=0)
    status = Column(String(20), default="open")  # open / adjusted
    handled_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.now)


# ---------- 阶段三：供应商 / 客户档案 ----------
class Supplier(Base):
    """供应商档案。"""

    __tablename__ = "suppliers"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    contact = Column(String(50))
    phone = Column(String(30))
    address = Column(String(200))
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, onupdate=datetime.now)


class Customer(Base):
    """客户档案。"""

    __tablename__ = "customers"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    contact = Column(String(50))
    phone = Column(String(30))
    address = Column(String(200))
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, onupdate=datetime.now)


# ---------- 阶段三：采购订单 ----------
class PurchaseOrder(Base):
    """采购订单：pending -> approved(审核) -> received(收货) / cancelled。"""

    __tablename__ = "purchase_orders"

    id = Column(Integer, primary_key=True)
    order_no = Column(String(30), unique=True, index=True, nullable=False)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False, index=True)
    status = Column(String(20), default="pending")  # pending / approved / received / cancelled
    total_amount = Column(Numeric(12, 2), nullable=False, default=0)
    remark = Column(String(255))
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.now, index=True)
    approved_at = Column(DateTime)
    received_at = Column(DateTime)


class PurchaseOrderItem(Base):
    """采购订单明细：每个产品收货到指定库位 zone_id，并记录单价与金额。"""

    __tablename__ = "purchase_order_item"

    id = Column(Integer, primary_key=True)
    purchase_order_id = Column(Integer, ForeignKey("purchase_orders.id"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    zone_id = Column(Integer, ForeignKey("zones.id"), nullable=False)
    quantity = Column(Integer, nullable=False, default=0)
    unit_price = Column(Numeric(12, 2), nullable=False, default=0)
    amount = Column(Numeric(12, 2), nullable=False, default=0)


# ---------- 阶段三：销售订单 ----------
class SalesOrder(Base):
    """销售订单：pending -> approved(审核) -> shipped(发货) / cancelled。"""

    __tablename__ = "sale_orders"

    id = Column(Integer, primary_key=True)
    order_no = Column(String(30), unique=True, index=True, nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False, index=True)
    status = Column(String(20), default="pending")  # pending / approved / shipped / cancelled
    total_amount = Column(Numeric(12, 2), nullable=False, default=0)
    remark = Column(String(255))
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.now, index=True)
    approved_at = Column(DateTime)
    shipped_at = Column(DateTime)


class SalesOrderItem(Base):
    """销售订单明细：从指定库位 zone_id 发出发货数量，并记录单价与金额。"""

    __tablename__ = "sale_order_item"

    id = Column(Integer, primary_key=True)
    sale_order_id = Column(Integer, ForeignKey("sale_orders.id"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    zone_id = Column(Integer, ForeignKey("zones.id"), nullable=False)
    quantity = Column(Integer, nullable=False, default=0)
    unit_price = Column(Numeric(12, 2), nullable=False, default=0)
    amount = Column(Numeric(12, 2), nullable=False, default=0)
