from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from src.database import get_db
from src.dependencies import require_permission
from src.pagination import paginate
from src.schemas import Page, Supplier, SupplierCreate, SupplierOut

router = APIRouter()


@router.post("/suppliers", response_model=SupplierOut)
def create_supplier(
    payload: SupplierCreate,
    db: Session = Depends(get_db),
    _: None = Depends(require_permission("supplier:write")),
):
    """创建供应商"""
    if db.query(Supplier).filter(Supplier.name == payload.name).first():
        raise HTTPException(status_code=400, detail=f"供应商「{payload.name}」已存在")
    supplier = Supplier(**payload.model_dump())
    db.add(supplier)
    db.commit()
    db.refresh(supplier)
    return supplier


@router.get("/suppliers", response_model=Page[SupplierOut])
def list_suppliers(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(1000, ge=1, le=1000),
    _: None = Depends(require_permission("supplier:read")),
):
    """分页获取所有供应商"""
    query = db.query(Supplier).order_by(Supplier.id.asc())
    return paginate(query, page, page_size)


@router.get("/suppliers/{id}", response_model=SupplierOut)
def get_supplier(
    id: int,
    db: Session = Depends(get_db),
    _: None = Depends(require_permission("supplier:read")),
):
    """获取单个供应商"""
    supplier = db.query(Supplier).filter(Supplier.id == id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="供应商不存在")
    return supplier


@router.put("/suppliers/{id}", response_model=SupplierOut)
def update_supplier(
    id: int,
    payload: SupplierCreate,
    db: Session = Depends(get_db),
    _: None = Depends(require_permission("supplier:write")),
):
    """更新供应商"""
    supplier = db.query(Supplier).filter(Supplier.id == id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="供应商不存在")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(supplier, key, value)
    db.commit()
    db.refresh(supplier)
    return supplier


@router.delete("/suppliers/{id}")
def delete_supplier(
    id: int,
    db: Session = Depends(get_db),
    _: None = Depends(require_permission("supplier:write")),
):
    """删除供应商"""
    supplier = db.query(Supplier).filter(Supplier.id == id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="供应商不存在")
    db.delete(supplier)
    db.commit()
    return {"message": "供应商已删除"}