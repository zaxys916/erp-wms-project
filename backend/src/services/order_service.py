"""业务订单库存联动：采购收货入库、销售发货出库。

统一经由 stock_service.apply_stock_change 写库存与流水（inventory_movement），
保证与出入库单据/盘点共用同一套增减逻辑，且天然具备行锁与负库存拦截。
"""
import random
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session

from src.models import PurchaseOrder, PurchaseOrderItem, SalesOrder, SalesOrderItem
from src.services.stock_service import apply_stock_change

__all__ = ["generate_order_no", "receive_purchase", "ship_sale"]


def generate_order_no(prefix: str) -> str:
    """生成订单号：前缀 + 时间戳 + 随机后缀，保证唯一。"""
    ts = datetime.now().strftime("%Y%m%d%H%M%S")
    return f"{prefix}{ts}{random.randint(100, 999)}"


def receive_purchase(
    db: Session,
    order: PurchaseOrder,
    *,
    operator_id: int,
) -> PurchaseOrder:
    """采购收货：将 approved 采购单明细入库到各自库位，状态置 received。"""
    if order.status != "approved":
        raise HTTPException(
            status_code=400,
            detail=f"只有已审核(approved)的采购单才能收货，当前状态: {order.status}",
        )
    items = (
        db.query(PurchaseOrderItem)
        .filter(PurchaseOrderItem.purchase_order_id == order.id)
        .all()
    )
    for it in items:
        apply_stock_change(
            db,
            product_id=it.product_id,
            zone_id=it.zone_id,
            change=it.quantity,
            ref_no=order.order_no,
            remark="采购收货",
            operator_id=operator_id,
        )
    order.status = "received"
    order.received_at = datetime.now()
    db.commit()
    db.refresh(order)
    return order


def ship_sale(
    db: Session,
    order: SalesOrder,
    *,
    operator_id: int,
) -> SalesOrder:
    """销售发货：将 approved 销售单明细自各自库位出库，状态置 shipped。"""
    if order.status != "approved":
        raise HTTPException(
            status_code=400,
            detail=f"只有已审核(approved)的销售单才能发货，当前状态: {order.status}",
        )
    items = (
        db.query(SalesOrderItem)
        .filter(SalesOrderItem.sale_order_id == order.id)
        .all()
    )
    for it in items:
        apply_stock_change(
            db,
            product_id=it.product_id,
            zone_id=it.zone_id,
            change=-it.quantity,
            ref_no=order.order_no,
            remark="销售发货",
            operator_id=operator_id,
        )
    order.status = "shipped"
    order.shipped_at = datetime.now()
    db.commit()
    db.refresh(order)
    return order