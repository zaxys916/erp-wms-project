from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from src.database import get_db
from src.dependencies import require_permission
from src.pagination import paginate
from src.schemas import (
    Inventory,
    InventoryCreate,
    InventoryMovement,
    InventoryMovementOut,
    InventoryOut,
    Page,
)
from src.services.stock_service import apply_stock_change, set_inventory

router = APIRouter()


def _get_record(db: Session, inventory_id: int) -> Inventory:
    record = db.query(Inventory).filter(Inventory.id == inventory_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Inventory record not found")
    return record


def _ensure_no_duplicate(db: Session, product_id: int, zone_id: int) -> None:
    exists = (
        db.query(Inventory)
        .filter(Inventory.product_id == product_id, Inventory.zone_id == zone_id)
        .first()
    )
    if exists:
        raise HTTPException(status_code=400, detail="该产品在该库位已有库存记录，请直接调整数量")


@router.post("/inventory", response_model=InventoryOut)
def create_inventory(
    inventory: InventoryCreate,
    db: Session = Depends(get_db),
    _: None = Depends(require_permission("inventory:write")),
):
    """新增库存记录（数量 > 0 时自动写一条 in 流水）"""
    _ensure_no_duplicate(db, inventory.product_id, inventory.zone_id)
    if inventory.quantity == 0:
        record = Inventory(**inventory.model_dump())
        db.add(record)
        db.commit()
        db.refresh(record)
        return record
    record = apply_stock_change(
        db,
        product_id=inventory.product_id,
        zone_id=inventory.zone_id,
        change=inventory.quantity,
        remark="手工新增库存记录",
    )
    db.commit()
    db.refresh(record)
    return record


@router.get("/inventory", response_model=Page[InventoryOut])
def get_all_inventory(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(1000, ge=1, le=1000),
    _: None = Depends(require_permission("inventory:read")),
):
    """分页获取所有库存记录"""
    query = db.query(Inventory).order_by(Inventory.id.asc())
    return paginate(query, page, page_size)


@router.get("/inventory/status")
def get_inventory_status(
    db: Session = Depends(get_db),
    _: None = Depends(require_permission("inventory:read")),
):
    """获取库存总览状态"""
    rows = db.query(Inventory).all()
    return {
        "total_records": len(rows),
        "total_quantity": sum(r.quantity for r in rows),
        "last_updated": max((r.last_updated for r in rows if r.last_updated), default=None),
    }


@router.get("/inventory/movements", response_model=Page[InventoryMovementOut])
def get_inventory_movements(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(1000, ge=1, le=1000),
    _: None = Depends(require_permission("movement:read")),
):
    """分页获取库存流水（最新在前）"""
    query = db.query(InventoryMovement).order_by(InventoryMovement.id.desc())
    return paginate(query, page, page_size)


@router.get("/inventory/{id}", response_model=InventoryOut)
def get_inventory(
    id: int,
    db: Session = Depends(get_db),
    _: None = Depends(require_permission("inventory:read")),
):
    """获取单条库存记录"""
    return _get_record(db, id)


@router.put("/inventory/{id}", response_model=InventoryOut)
def update_inventory(
    id: int,
    inventory_update: InventoryCreate,
    db: Session = Depends(get_db),
    _: None = Depends(require_permission("inventory:write")),
):
    """更新库存数量为目标值（差额在行锁内计算并写 adjust 流水，保证可追溯）"""
    record = _get_record(db, id)
    if inventory_update.product_id != record.product_id or inventory_update.zone_id != record.zone_id:
        raise HTTPException(status_code=400, detail="不允许通过更新接口迁移产品/库位")

    record = set_inventory(
        db,
        product_id=record.product_id,
        zone_id=record.zone_id,
        target_qty=inventory_update.quantity,
        ref_no=f"INV#{record.id}",
        remark="手工调整库存数量",
    )
    db.commit()
    db.refresh(record)
    return record


@router.delete("/inventory/{id}")
def delete_inventory(
    id: int,
    db: Session = Depends(get_db),
    _: None = Depends(require_permission("inventory:write")),
):
    """删除库存记录（在行锁内取最新余量记出库流水后删除）"""
    record = (
        db.query(Inventory)
        .filter(Inventory.id == id)
        .with_for_update()
        .first()
    )
    if not record:
        raise HTTPException(status_code=404, detail="Inventory record not found")
    if record.quantity and record.quantity > 0:
        apply_stock_change(
            db,
            product_id=record.product_id,
            zone_id=record.zone_id,
            change=-record.quantity,
            ref_no=f"INV#{record.id}",
            remark="删除库存记录",
        )
    db.delete(record)
    db.commit()
    return {"message": "Inventory deleted successfully"}
