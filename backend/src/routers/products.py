from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from src.database import get_db
from src.dependencies import require_permission
from src.pagination import paginate
from src.schemas import Page, Product, ProductCreate, ProductOut

router = APIRouter()


@router.post("/products", response_model=ProductOut)
def create_product(
    product: ProductCreate,
    db: Session = Depends(get_db),
    _: None = Depends(require_permission("product:write")),
):
    """创建新产品"""
    new_product = Product(**product.model_dump())
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    return new_product


@router.get("/products", response_model=Page[ProductOut])
def get_all_products(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(1000, ge=1, le=1000),
    _: None = Depends(require_permission("product:read")),
):
    """分页获取所有产品"""
    query = db.query(Product).order_by(Product.id.asc())
    return paginate(query, page, page_size)


@router.get("/products/{id}", response_model=ProductOut)
def get_product(
    id: int,
    db: Session = Depends(get_db),
    _: None = Depends(require_permission("product:read")),
):
    """获取单个产品"""
    product = db.query(Product).filter(Product.id == id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.put("/products/{id}", response_model=ProductOut)
def update_product(
    id: int,
    product_update: ProductCreate,
    db: Session = Depends(get_db),
    _: None = Depends(require_permission("product:write")),
):
    """更新产品信息"""
    product = db.query(Product).filter(Product.id == id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    for key, value in product_update.model_dump(exclude_unset=True).items():
        setattr(product, key, value)

    db.commit()
    db.refresh(product)
    return product


@router.delete("/products/{id}")
def delete_product(
    id: int,
    db: Session = Depends(get_db),
    _: None = Depends(require_permission("product:write")),
):
    """删除产品"""
    product = db.query(Product).filter(Product.id == id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    db.delete(product)
    db.commit()
    return {"message": "Product deleted successfully"}
