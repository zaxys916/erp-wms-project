from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.database import get_db
from src.dependencies import require_permission
from src.schemas import Zone, ZoneCreate, ZoneOut

router = APIRouter()


@router.post("/zones", response_model=ZoneOut)
def create_zone(
    zone: ZoneCreate,
    db: Session = Depends(get_db),
    _: None = Depends(require_permission("zone:write")),
):
    """创建新库位"""
    new_zone = Zone(**zone.model_dump())
    db.add(new_zone)
    db.commit()
    db.refresh(new_zone)
    return new_zone


@router.get("/zones", response_model=List[ZoneOut])
def get_all_zones(
    db: Session = Depends(get_db),
    _: None = Depends(require_permission("zone:read")),
):
    """获取所有库位"""
    return db.query(Zone).all()


@router.get("/zones/{id}", response_model=ZoneOut)
def get_zone(
    id: int,
    db: Session = Depends(get_db),
    _: None = Depends(require_permission("zone:read")),
):
    """获取单个库位"""
    zone = db.query(Zone).filter(Zone.id == id).first()
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")
    return zone


@router.put("/zones/{id}", response_model=ZoneOut)
def update_zone(
    id: int,
    zone_update: ZoneCreate,
    db: Session = Depends(get_db),
    _: None = Depends(require_permission("zone:write")),
):
    """更新库位信息"""
    zone = db.query(Zone).filter(Zone.id == id).first()
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")

    for key, value in zone_update.model_dump(exclude_unset=True).items():
        setattr(zone, key, value)

    db.commit()
    db.refresh(zone)
    return zone


@router.put("/zones/{id}/enable", response_model=ZoneOut)
def enable_zone(
    id: int,
    db: Session = Depends(get_db),
    _: None = Depends(require_permission("zone:write")),
):
    """启用库位"""
    zone = db.query(Zone).filter(Zone.id == id).first()
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")

    zone.status = True
    db.commit()
    db.refresh(zone)
    return zone


@router.put("/zones/{id}/disable", response_model=ZoneOut)
def disable_zone(
    id: int,
    db: Session = Depends(get_db),
    _: None = Depends(require_permission("zone:write")),
):
    """禁用库位"""
    zone = db.query(Zone).filter(Zone.id == id).first()
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")

    zone.status = False
    db.commit()
    db.refresh(zone)
    return zone


@router.delete("/zones/{id}")
def delete_zone(
    id: int,
    db: Session = Depends(get_db),
    _: None = Depends(require_permission("zone:write")),
):
    """删除库位"""
    zone = db.query(Zone).filter(Zone.id == id).first()
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")

    db.delete(zone)
    db.commit()
    return {"message": "Zone deleted successfully"}
