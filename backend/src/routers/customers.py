from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from src.database import get_db
from src.dependencies import require_permission
from src.pagination import paginate
from src.schemas import Customer, CustomerCreate, CustomerOut, Page

router = APIRouter()


@router.post("/customers", response_model=CustomerOut)
def create_customer(
    payload: CustomerCreate,
    db: Session = Depends(get_db),
    _: None = Depends(require_permission("customer:write")),
):
    """创建客户"""
    if db.query(Customer).filter(Customer.name == payload.name).first():
        raise HTTPException(status_code=400, detail=f"客户「{payload.name}」已存在")
    customer = Customer(**payload.model_dump())
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


@router.get("/customers", response_model=Page[CustomerOut])
def list_customers(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(1000, ge=1, le=1000),
    _: None = Depends(require_permission("customer:read")),
):
    """分页获取所有客户"""
    query = db.query(Customer).order_by(Customer.id.asc())
    return paginate(query, page, page_size)


@router.get("/customers/{id}", response_model=CustomerOut)
def get_customer(
    id: int,
    db: Session = Depends(get_db),
    _: None = Depends(require_permission("customer:read")),
):
    """获取单个客户"""
    customer = db.query(Customer).filter(Customer.id == id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="客户不存在")
    return customer


@router.put("/customers/{id}", response_model=CustomerOut)
def update_customer(
    id: int,
    payload: CustomerCreate,
    db: Session = Depends(get_db),
    _: None = Depends(require_permission("customer:write")),
):
    """更新客户"""
    customer = db.query(Customer).filter(Customer.id == id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="客户不存在")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(customer, key, value)
    db.commit()
    db.refresh(customer)
    return customer


@router.delete("/customers/{id}")
def delete_customer(
    id: int,
    db: Session = Depends(get_db),
    _: None = Depends(require_permission("customer:write")),
):
    """删除客户"""
    customer = db.query(Customer).filter(Customer.id == id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="客户不存在")
    db.delete(customer)
    db.commit()
    return {"message": "客户已删除"}