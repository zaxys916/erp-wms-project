"""库存盘点：创建盘点单（冻结账面快照）、录入实际数、完成盘点生成差异并调账。

盘点完成后，差异非零的明细自动写入 discrepancies 差异报告，并同步调整库存（adjust 流水）。
"""
from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from src.database import get_db
from src.dependencies import require_permission
from src.models import (
    Discrepancy,
    Inventory,
    Stocktaking,
    StocktakingItem,
    User,
    Zone,
)
from src.pagination import paginate
from src.schemas import (
    DiscrepancyOut,
    Page,
    StocktakingCreate,
    StocktakingDetail,
    StocktakingItemOut,
    StocktakingItemUpdate,
    StocktakingOut,
)
from src.services.stock_service import set_inventory

router = APIRouter()


def _gen_order_no() -> str:
    return f"ST{datetime.now():%Y%m%d}{uuid4().hex[:6].upper()}"


def _get_stocktaking(db: Session, stocktaking_id: int) -> Stocktaking:
    st = db.query(Stocktaking).filter(Stocktaking.id == stocktaking_id).first()
    if not st:
        raise HTTPException(status_code=404, detail="盘点单不存在")
    return st


def _get_item(db: Session, stocktaking: Stocktaking, item_id: int) -> StocktakingItem:
    item = (
        db.query(StocktakingItem)
        .filter(
            StocktakingItem.id == item_id,
            StocktakingItem.stocktaking_id == stocktaking.id,
        )
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="盘点明细不存在")
    return item


def _ensure_pending(stocktaking: Stocktaking) -> None:
    if stocktaking.status != "pending":
        raise HTTPException(status_code=400, detail="盘点单已完结，不可再操作")


@router.post("/stocktakes", response_model=StocktakingDetail)
def create_stocktaking(
    payload: StocktakingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("stocktake:write")),
):
    """创建盘点单：按库位（zone_id 为空则全仓）冻结当前库存快照"""
    if payload.zone_id is not None:
        zone = db.query(Zone).filter(Zone.id == payload.zone_id).first()
        if not zone:
            raise HTTPException(status_code=404, detail="库位不存在")
        query = db.query(Inventory).filter(Inventory.zone_id == payload.zone_id)
    else:
        query = db.query(Inventory)

    records = query.all()
    if not records:
        raise HTTPException(status_code=400, detail="无可盘点的库存记录")

    stocktaking = Stocktaking(
        order_no=_gen_order_no(),
        zone_id=payload.zone_id,
        remark=payload.remark,
        status="pending",
        created_by=current_user.id,
    )
    db.add(stocktaking)
    db.flush()
    for rec in records:
        db.add(
            StocktakingItem(
                stocktaking_id=stocktaking.id,
                product_id=rec.product_id,
                zone_id=rec.zone_id,
                book_qty=rec.quantity or 0,
                actual_qty=None,
                diff=0,
            )
        )
    db.commit()

    detail = StocktakingDetail.model_validate(stocktaking)
    detail.items = [
        StocktakingItemOut.model_validate(i)
        for i in db.query(StocktakingItem)
        .filter(StocktakingItem.stocktaking_id == stocktaking.id)
        .all()
    ]
    return detail


@router.get("/stocktakes", response_model=Page[StocktakingOut])
def list_stocktakes(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(1000, ge=1, le=1000),
    _: None = Depends(require_permission("stocktake:read")),
):
    """盘点单列表（最新在前）"""
    query = db.query(Stocktaking).order_by(Stocktaking.id.desc())
    return paginate(query, page, page_size)


@router.get("/stocktakes/discrepancies", response_model=Page[DiscrepancyOut])
def list_discrepancies(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(1000, ge=1, le=1000),
    _: None = Depends(require_permission("stocktake:read")),
):
    """盘点差异报告列表（最新在前）"""
    query = db.query(Discrepancy).order_by(Discrepancy.id.desc())
    return paginate(query, page, page_size)


@router.get("/stocktakes/{id}", response_model=StocktakingDetail)
def get_stocktaking(
    id: int,
    db: Session = Depends(get_db),
    _: None = Depends(require_permission("stocktake:read")),
):
    """盘点单详情（含全部明细）"""
    stocktaking = _get_stocktaking(db, id)
    detail = StocktakingDetail.model_validate(stocktaking)
    detail.items = [
        StocktakingItemOut.model_validate(i)
        for i in db.query(StocktakingItem)
        .filter(StocktakingItem.stocktaking_id == id)
        .all()
    ]
    return detail


@router.put("/stocktakes/{id}/items/{item_id}", response_model=StocktakingItemOut)
def update_item_actual(
    id: int,
    item_id: int,
    payload: StocktakingItemUpdate,
    db: Session = Depends(get_db),
    _: None = Depends(require_permission("stocktake:write")),
):
    """录入某个产品的实际盘点数量"""
    stocktaking = _get_stocktaking(db, id)
    _ensure_pending(stocktaking)
    item = _get_item(db, stocktaking, item_id)
    item.actual_qty = payload.actual_qty
    item.diff = payload.actual_qty - (item.book_qty or 0)
    db.commit()
    db.refresh(item)
    return item


@router.post("/stocktakes/{id}/complete")
def complete_stocktaking(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("stocktake:write")),
):
    """完成盘点：按实际数调整库存、为差异生成差异报告、写 adjust 流水"""
    stocktaking = _get_stocktaking(db, id)
    _ensure_pending(stocktaking)

    items = (
        db.query(StocktakingItem)
        .filter(StocktakingItem.stocktaking_id == id)
        .all()
    )
    adjusted = 0
    total_diff = 0
    for item in items:
        actual = item.actual_qty if item.actual_qty is not None else item.book_qty
        item.actual_qty = actual
        item.diff = actual - item.book_qty
        total_diff += item.diff
        if item.diff != 0:
            set_inventory(
                db,
                product_id=item.product_id,
                zone_id=item.zone_id,
                target_qty=actual,
                ref_no=stocktaking.order_no,
                remark="盘点差异调整",
                operator_id=current_user.id,
            )
            db.add(
                Discrepancy(
                    stocktaking_id=stocktaking.id,
                    product_id=item.product_id,
                    zone_id=item.zone_id,
                    book_qty=item.book_qty,
                    actual_qty=actual,
                    difference=item.diff,
                    status="open",
                )
            )
            adjusted += 1

    stocktaking.status = "completed"
    stocktaking.completed_at = datetime.now()
    db.commit()
    return {
        "id": stocktaking.id,
        "order_no": stocktaking.order_no,
        "status": stocktaking.status,
        "item_count": len(items),
        "adjusted_count": adjusted,
        "total_diff": total_diff,
    }
