from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from src.database import get_db
from src.dependencies import require_permission
from src.models import Product, PurchaseOrder, PurchaseOrderItem, Supplier, User, Zone
from src.pagination import paginate
from src.schemas import (
    Page,
    PurchaseOrderCreate,
    PurchaseOrderDetail,
    PurchaseOrderItemIn,
    PurchaseOrderOut,
)
from src.services.order_service import generate_order_no, receive_purchase

router = APIRouter()


def _build_items(
    db: Session, items: list[PurchaseOrderItemIn], order: PurchaseOrder
) -> None:
    """校验产品/库位存在并写入订单明细（amount = quantity * unit_price）。"""
    for it in items:
        if not db.query(Product).filter(Product.id == it.product_id).first():
            raise HTTPException(status_code=400, detail=f"产品不存在: #{it.product_id}")
        if not db.query(Zone).filter(Zone.id == it.zone_id).first():
            raise HTTPException(status_code=400, detail=f"库位不存在: #{it.zone_id}")
        db.add(
            PurchaseOrderItem(
                purchase_order_id=order.id,
                product_id=it.product_id,
                zone_id=it.zone_id,
                quantity=it.quantity,
                unit_price=it.unit_price,
                amount=Decimal(it.quantity) * it.unit_price,
            )
        )


@router.post("/purchases", response_model=PurchaseOrderDetail)
def create_purchase_order(
    payload: PurchaseOrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("purchase:write")),
):
    """创建采购订单（含明细）"""
    supplier = db.query(Supplier).filter(Supplier.id == payload.supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=400, detail=f"供应商不存在: #{payload.supplier_id}")

    total = sum(
        (Decimal(it.quantity) * it.unit_price for it in payload.items),
        Decimal("0"),
    )
    order = PurchaseOrder(
        order_no=generate_order_no("PO"),
        supplier_id=payload.supplier_id,
        status="pending",
        total_amount=total,
        remark=payload.remark,
        created_by=current_user.id,
    )
    db.add(order)
    db.flush()
    _build_items(db, payload.items, order)
    db.commit()
    return _detail(db, order.id)


@router.get("/purchases", response_model=Page[PurchaseOrderOut])
def list_purchase_orders(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(1000, ge=1, le=1000),
    _: None = Depends(require_permission("purchase:read")),
):
    """分页获取采购订单"""
    query = db.query(PurchaseOrder).order_by(PurchaseOrder.id.desc())
    return paginate(query, page, page_size)


@router.get("/purchases/{id}", response_model=PurchaseOrderDetail)
def get_purchase_order(
    id: int,
    db: Session = Depends(get_db),
    _: None = Depends(require_permission("purchase:read")),
):
    """获取采购订单详情（含明细）"""
    order = db.query(PurchaseOrder).filter(PurchaseOrder.id == id).first()
    if not order:
        raise HTTPException(status_code=404, detail="采购订单不存在")
    return _detail(db, id)


@router.post("/purchases/{id}/approve", response_model=PurchaseOrderDetail)
def approve_purchase_order(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("purchase:write")),
):
    """审核采购订单：pending -> approved"""
    order = db.query(PurchaseOrder).filter(PurchaseOrder.id == id).first()
    if not order:
        raise HTTPException(status_code=404, detail="采购订单不存在")
    if order.status != "pending":
        raise HTTPException(status_code=400, detail=f"仅待审核(pending)订单可审核，当前: {order.status}")
    order.status = "approved"
    order.approved_by = current_user.id
    order.approved_at = datetime.now()
    db.commit()
    return _detail(db, id)


@router.post("/purchases/{id}/receive", response_model=PurchaseOrderDetail)
def receive_purchase_order(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("purchase:write")),
):
    """收货入库：approved -> received，按明细增加库存并写流水"""
    order = db.query(PurchaseOrder).filter(PurchaseOrder.id == id).first()
    if not order:
        raise HTTPException(status_code=404, detail="采购订单不存在")
    receive_purchase(db, order, operator_id=current_user.id)
    return _detail(db, id)


@router.post("/purchases/{id}/cancel", response_model=PurchaseOrderDetail)
def cancel_purchase_order(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("purchase:write")),
):
    """取消采购订单：仅 pending 可取消"""
    order = db.query(PurchaseOrder).filter(PurchaseOrder.id == id).first()
    if not order:
        raise HTTPException(status_code=404, detail="采购订单不存在")
    if order.status != "pending":
        raise HTTPException(status_code=400, detail=f"仅待审核(pending)订单可取消，当前: {order.status}")
    order.status = "cancelled"
    db.commit()
    return _detail(db, id)


def _detail(db: Session, order_id: int) -> PurchaseOrder:
    order = db.query(PurchaseOrder).filter(PurchaseOrder.id == order_id).first()
    order.items = (
        db.query(PurchaseOrderItem)
        .filter(PurchaseOrderItem.purchase_order_id == order_id)
        .all()
    )
    return order