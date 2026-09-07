"""出入库单据：入库单/出库单的创建、审核（生效）、驳回、取消。

单据审核通过后才真正变动库存，并写入库存流水（inventory_movement）。
"""
from datetime import datetime
from typing import List
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.database import get_db
from src.dependencies import require_permission
from src.models import StockOrder, User
from src.schemas import StockOrderCreate, StockOrderOut
from src.services.stock_service import apply_stock_change

router = APIRouter()


def _gen_order_no(order_type: str) -> str:
    prefix = "IN" if order_type == "in" else "OUT"
    return f"{prefix}{datetime.now():%Y%m%d}{uuid4().hex[:6].upper()}"


def _get_order(db: Session, order_id: int) -> StockOrder:
    order = db.query(StockOrder).filter(StockOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="单据不存在")
    return order


def _ensure_pending(order: StockOrder) -> None:
    if order.status != "pending":
        raise HTTPException(status_code=400, detail=f"单据当前状态为 {order.status}，不可操作")


@router.post("/movements", response_model=StockOrderOut)
def create_order(
    payload: StockOrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("inventory:write")),
):
    """创建入库/出库单（pending，待审核）"""
    order = StockOrder(
        order_no=_gen_order_no(payload.order_type),
        order_type=payload.order_type,
        product_id=payload.product_id,
        zone_id=payload.zone_id,
        quantity=payload.quantity,
        remark=payload.remark,
        created_by=current_user.id,
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


@router.get("/movements", response_model=List[StockOrderOut])
def list_orders(
    db: Session = Depends(get_db),
    _: None = Depends(require_permission("inventory:read")),
):
    """单据列表（最新在前）"""
    return db.query(StockOrder).order_by(StockOrder.id.desc()).limit(200).all()


@router.get("/movements/{id}", response_model=StockOrderOut)
def get_order(
    id: int,
    db: Session = Depends(get_db),
    _: None = Depends(require_permission("inventory:read")),
):
    """单据详情"""
    return _get_order(db, id)


@router.post("/movements/{id}/approve", response_model=StockOrderOut)
def approve_order(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("inventory:write")),
):
    """审核通过：按单据方向增减库存并写流水"""
    order = _get_order(db, id)
    _ensure_pending(order)

    change = order.quantity if order.order_type == "in" else -order.quantity
    apply_stock_change(
        db,
        product_id=order.product_id,
        zone_id=order.zone_id,
        change=change,
        ref_no=order.order_no,
        remark=("入库单审核" if order.order_type == "in" else "出库单审核"),
        operator_id=current_user.id,
    )
    order.status = "approved"
    order.approved_by = current_user.id
    order.approved_at = datetime.now()
    db.commit()
    db.refresh(order)
    return order


@router.post("/movements/{id}/reject", response_model=StockOrderOut)
def reject_order(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("inventory:write")),
):
    """驳回单据"""
    order = _get_order(db, id)
    _ensure_pending(order)
    order.status = "rejected"
    order.approved_by = current_user.id
    order.approved_at = datetime.now()
    db.commit()
    db.refresh(order)
    return order


@router.post("/movements/{id}/cancel", response_model=StockOrderOut)
def cancel_order(
    id: int,
    db: Session = Depends(get_db),
    _: None = Depends(require_permission("inventory:write")),
):
    """取消待审核单据"""
    order = _get_order(db, id)
    _ensure_pending(order)
    order.status = "cancelled"
    db.commit()
    db.refresh(order)
    return order
