"""库存变动核心逻辑：增减库存并写入流水（inventory_movement）。

所有会改变库存数量或库位余额的接口都应经由 apply_stock_change / set_inventory
走此模块，从而保证库存流水完整、可追溯。
"""
from datetime import datetime
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from src.models import Inventory, InventoryMovement

MOVEMENT_IN = "in"
MOVEMENT_OUT = "out"
MOVEMENT_ADJUST = "adjust"


def _movement_type_for(change: int) -> str:
    """根据数量变化方向推导流水类型（正的为 in，负的为 out）。"""
    return MOVEMENT_IN if change > 0 else MOVEMENT_OUT


def apply_stock_change(
    db: Session,
    *,
    product_id: int,
    zone_id: int,
    change: int,
    movement_type: Optional[str] = None,
    ref_no: Optional[str] = None,
    remark: Optional[str] = None,
    operator_id: Optional[int] = None,
) -> Inventory:
    """按增量 change（可正可负）调整库存，并写一条流水。

    若目标库位尚无该产品的库存记录：
      - 增加库存时自动创建记录；
      - 减少库存时抛 400（不允许负库存出库）。
    """
    if change == 0:
        raise HTTPException(status_code=400, detail="变动数量不能为 0")

    # SELECT ... FOR UPDATE 行锁：并发审核同一出库单时串行化，避免超卖
    record = (
        db.query(Inventory)
        .filter(Inventory.product_id == product_id, Inventory.zone_id == zone_id)
        .with_for_update()
        .first()
    )
    if record is None:
        if change < 0:
            raise HTTPException(
                status_code=400,
                detail=f"该库位无产品 #{product_id} 的库存记录，无法出库",
            )
        record = Inventory(product_id=product_id, zone_id=zone_id, quantity=0)
        db.add(record)
        db.flush()

    new_qty = record.quantity + change
    if new_qty < 0:
        raise HTTPException(
            status_code=400,
            detail=f"库存不足：当前 {record.quantity}，本次出库 {abs(change)}",
        )

    record.quantity = new_qty
    record.last_updated = datetime.now()
    db.flush()

    db.add(
        InventoryMovement(
            product_id=product_id,
            zone_id=zone_id,
            movement_type=movement_type or _movement_type_for(change),
            quantity=abs(change),
            balance_after=new_qty,
            ref_no=ref_no,
            remark=remark,
            created_by=operator_id,
        )
    )
    return record


def set_inventory(
    db: Session,
    *,
    product_id: int,
    zone_id: int,
    target_qty: int,
    ref_no: Optional[str] = None,
    remark: Optional[str] = None,
    operator_id: Optional[int] = None,
) -> Inventory:
    """直接把某产品×库位的库存设为 target_qty（差额在行锁内计算并写 adjust 流水）。"""
    # 先取行锁，保证后续按目标量计算差额时没有并发写入插队
    record = (
        db.query(Inventory)
        .filter(Inventory.product_id == product_id, Inventory.zone_id == zone_id)
        .with_for_update()
        .first()
    )
    current = record.quantity if record else 0
    diff = target_qty - current
    if diff != 0:
        return apply_stock_change(
            db,
            product_id=product_id,
            zone_id=zone_id,
            change=diff,
            movement_type=MOVEMENT_ADJUST,
            ref_no=ref_no,
            remark=remark or "盘点/手工调整库存",
            operator_id=operator_id,
        )
    return record
