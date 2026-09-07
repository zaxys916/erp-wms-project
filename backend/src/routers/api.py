from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.database import get_db
from src.dependencies import require_permission
from src.schemas import Warehouse, WarehouseCreate, WarehouseOut

router = APIRouter()


@router.post("/warehouses", response_model=WarehouseOut)
def create_warehouse(
    warehouse: WarehouseCreate,
    db: Session = Depends(get_db),
    _: None = Depends(require_permission("warehouse:write")),
):
    """创建新仓库（仅管理员）"""
    new_warehouse = Warehouse(**warehouse.model_dump())
    db.add(new_warehouse)
    db.commit()
    db.refresh(new_warehouse)
    return new_warehouse


@router.get("/warehouses", response_model=List[WarehouseOut])
def get_all_warehouses(
    db: Session = Depends(get_db),
    _: None = Depends(require_permission("warehouse:read")),
):
    """获取所有仓库"""
    return db.query(Warehouse).all()


@router.get("/warehouses/{id}", response_model=WarehouseOut)
def get_warehouse(
    id: int,
    db: Session = Depends(get_db),
    _: None = Depends(require_permission("warehouse:read")),
):
    """获取单个仓库"""
    warehouse = db.query(Warehouse).filter(Warehouse.id == id).first()
    if not warehouse:
        raise HTTPException(status_code=404, detail="Warehouse not found")
    return warehouse


@router.put("/warehouses/{id}", response_model=WarehouseOut)
def update_warehouse(
    id: int,
    warehouse_update: WarehouseCreate,
    db: Session = Depends(get_db),
    _: None = Depends(require_permission("warehouse:write")),
):
    """更新仓库信息（仅管理员）"""
    warehouse = db.query(Warehouse).filter(Warehouse.id == id).first()
    if not warehouse:
        raise HTTPException(status_code=404, detail="Warehouse not found")

    for key, value in warehouse_update.model_dump(exclude_unset=True).items():
        setattr(warehouse, key, value)

    db.commit()
    db.refresh(warehouse)
    return warehouse


@router.delete("/warehouses/{id}")
def delete_warehouse(
    id: int,
    db: Session = Depends(get_db),
    _: None = Depends(require_permission("warehouse:write")),
):
    """删除仓库（仅管理员）"""
    warehouse = db.query(Warehouse).filter(Warehouse.id == id).first()
    if not warehouse:
        raise HTTPException(status_code=404, detail="Warehouse not found")

    db.delete(warehouse)
    db.commit()
    return {"message": "Warehouse deleted successfully"}
