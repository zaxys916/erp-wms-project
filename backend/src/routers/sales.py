from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from src.database import get_db
from src.dependencies import require_permission
from src.models import Customer, Product, SalesOrder, SalesOrderItem, User, Zone
from src.pagination import paginate
from src.schemas import (
    Page,
    SalesOrderCreate,
    SalesOrderDetail,
    SalesOrderItemIn,
    SalesOrderOut,
)
from src.services.order_service import generate_order_no, ship_sale

router = APIRouter()


def _detail(db: Session, order_id: int) -> SalesOrder:
    order = db.query(SalesOrder).filter(SalesOrder.id == order_id).first()
    order.items = (
        db.query(SalesOrderItem)
        .filter(SalesOrderItem.sale_order_id == order_id)
        .all()
    )
    return order


@router.post("/sales", response_model=SalesOrderDetail)
def create_sales_order(
    payload: SalesOrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("sale:write")),
):
    """创建销售订单（含明细）"""
    customer = db.query(Customer).filter(Customer.id == payload.customer_id).first()
    if not customer:
        raise HTTPException(status_code=400, detail=f"客户不存在: #{payload.customer_id}")

    total = sum(
        (Decimal(it.quantity) * it.unit_price for it in payload.items),
        Decimal("0"),
    )
    order = SalesOrder(
        order_no=generate_order_no("SO"),
        customer_id=payload.customer_id,
        status="pending",
        total_amount=total,
        remark=payload.remark,
        created_by=current_user.id,
    )
    db.add(order)
    db.flush()
    for it in payload.items:
        if not db.query(Product).filter(Product.id == it.product_id).first():
            raise HTTPException(status_code=400, detail=f"产品不存在: #{it.product_id}")
        if not db.query(Zone).filter(Zone.id == it.zone_id).first():
            raise HTTPException(status_code=400, detail=f"库位不存在: #{it.zone_id}")
        db.add(
            SalesOrderItem(
                sale_order_id=order.id,
                product_id=it.product_id,
                zone_id=it.zone_id,
                quantity=it.quantity,
                unit_price=it.unit_price,
                amount=Decimal(it.quantity) * it.unit_price,
            )
        )
    db.commit()
    return _detail(db, order.id)


@router.get("/sales", response_model=Page[SalesOrderOut])
def list_sales_orders(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(1000, ge=1, le=1000),
    _: None = Depends(require_permission("sale:read")),
):
    """分页获取销售订单"""
    query = db.query(SalesOrder).order_by(SalesOrder.id.desc())
    return paginate(query, page, page_size)


@router.get("/sales/{id}", response_model=SalesOrderDetail)
def get_sales_order(
    id: int,
    db: Session = Depends(get_db),
    _: None = Depends(require_permission("sale:read")),
):
    """获取销售订单详情（含明细）"""
    order = db.query(SalesOrder).filter(SalesOrder.id == id).first()
    if not order:
        raise HTTPException(status_code=404, detail="销售订单不存在")
    return _detail(db, id)


@router.post("/sales/{id}/approve", response_model=SalesOrderDetail)
def approve_sales_order(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("sale:write")),
):
    """审核销售订单：pending -> approved"""
    order = db.query(SalesOrder).filter(SalesOrder.id == id).first()
    if not order:
        raise HTTPException(status_code=404, detail="销售订单不存在")
    if order.status != "pending":
        raise HTTPException(status_code=400, detail=f"仅待审核(pending)订单可审核，当前: {order.status}")
    order.status = "approved"
    order.approved_by = current_user.id
    order.approved_at = datetime.now()
    db.commit()
    return _detail(db, id)


@router.post("/sales/{id}/ship", response_model=SalesOrderDetail)
def ship_sales_order(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("sale:write")),
):
    """发货出库：approved -> shipped，按明细扣减库存并写流水"""
    order = db.query(SalesOrder).filter(SalesOrder.id == id).first()
    if not order:
        raise HTTPException(status_code=404, detail="销售订单不存在")
    ship_sale(db, order, operator_id=current_user.id)
    return _detail(db, id)


@router.post("/sales/{id}/cancel", response_model=SalesOrderDetail)
def cancel_sales_order(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("sale:write")),
):
    """取消销售订单：仅 pending 可取消"""
    order = db.query(SalesOrder).filter(SalesOrder.id == id).first()
    if not order:
        raise HTTPException(status_code=404, detail="销售订单不存在")
    if order.status != "pending":
        raise HTTPException(status_code=400, detail=f"仅待审核(pending)订单可取消，当前: {order.status}")
    order.status = "cancelled"
    db.commit()
    return _detail(db, id)