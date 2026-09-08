"""报表统计与安全库存预警（阶段三）。

- 库存总量/价值统计
- 出入库趋势
- 采购/销售订单统计
- 安全库存预警清单
"""
from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from src.database import get_db
from src.dependencies import require_permission
from src.models import (
    Inventory,
    InventoryMovement,
    Product,
    PurchaseOrder,
    SalesOrder,
)

router = APIRouter()

ALERT_PERMISSION = require_permission("alert:read")
REPORT_PERMISSION = require_permission("report:read")


@router.get("/reports/inventory-summary")
def inventory_summary(
    db: Session = Depends(get_db),
    _: None = Depends(REPORT_PERMISSION),
):
    """库存总量与库存价值统计（RPT-01）。"""
    total_records = db.query(func.count(Inventory.id)).scalar() or 0
    total_quantity = db.query(func.coalesce(func.sum(Inventory.quantity), 0)).scalar() or 0
    inventory_value = (
        db.query(func.coalesce(func.sum(Inventory.quantity * Product.cost), 0))
        .select_from(Inventory)
        .join(Product, Product.id == Inventory.product_id)
        .scalar()
        or 0
    )
    product_count = db.query(func.count(Product.id)).scalar() or 0
    return {
        "total_records": total_records,
        "total_quantity": int(total_quantity),
        "product_count": product_count,
        "inventory_value": float(inventory_value),
    }


@router.get("/reports/movement-trend")
def movement_trend(
    db: Session = Depends(get_db),
    days: int = Query(30, ge=1, le=365),
    _: None = Depends(REPORT_PERMISSION),
):
    """近 N 天出入库趋势（RPT-02）：按天汇总 in / out 数量。"""
    since = date.today() - timedelta(days=days - 1)
    rows = (
        db.query(
            func.date(InventoryMovement.created_at).label("day"),
            InventoryMovement.movement_type,
            func.sum(InventoryMovement.quantity).label("qty"),
        )
        .filter(InventoryMovement.created_at >= since)
        .group_by("day", InventoryMovement.movement_type)
        .all()
    )
    bucket = {}
    for r in rows:
        d = str(r.day)
        bucket.setdefault(d, {"date": d, "in_qty": 0, "out_qty": 0})
        bucket[d][("in" if r.movement_type == "in" else "out") + "_qty"] = int(r.qty or 0)
    return sorted(bucket.values(), key=lambda x: x["date"])


@router.get("/reports/order-stats")
def order_stats(
    db: Session = Depends(get_db),
    since: date = None,
    until: date = None,
    _: None = Depends(REPORT_PERMISSION),
):
    """采购/销售订单统计（RPT-03）：按状态计数与金额汇总。"""
    def _orders(model):
        query = db.query(
            model.status,
            func.count(model.id).label("count"),
            func.coalesce(func.sum(model.total_amount), 0).label("amount"),
        )
        if since is not None:
            query = query.filter(model.created_at >= since)
        if until is not None:
            udt = until + timedelta(days=1)
            query = query.filter(model.created_at < udt)
        return query.group_by(model.status).all()

    return {
        "purchase": [
            {"status": s, "count": c, "amount": float(a)} for s, c, a in _orders(PurchaseOrder)
        ],
        "sale": [
            {"status": s, "count": c, "amount": float(a)} for s, c, a in _orders(SalesOrder)
        ],
    }


@router.get("/reports/stock-alerts")
def stock_alerts(
    db: Session = Depends(get_db),
    _: None = Depends(ALERT_PERMISSION),
):
    """安全库存预警清单（INV-05 / RPT-04）：产品总库存低于安全库存阈值。"""
    rows = (
        db.query(
            Product.id.label("product_id"),
            Product.name,
            Product.sku,
            Product.safety_stock,
            func.coalesce(func.sum(Inventory.quantity), 0).label("total_qty"),
        )
        .outerjoin(Inventory, Inventory.product_id == Product.id)
        .group_by(Product.id)
        .having(func.coalesce(func.sum(Inventory.quantity), 0) < Product.safety_stock)
        .order_by(Product.id.asc())
        .all()
    )
    return [
        {
            "product_id": r.product_id,
            "name": r.name,
            "sku": r.sku,
            "total_qty": int(r.total_qty),
            "safety_stock": r.safety_stock,
            "deficit": r.safety_stock - int(r.total_qty),
        }
        for r in rows
    ]