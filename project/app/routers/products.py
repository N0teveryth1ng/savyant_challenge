from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.database import get_db
from app.dependencies import require_admin
from app.services import product_service

router = APIRouter(prefix="/products", tags=["products"])


class ProductData(BaseModel):
    product_code: str
    name: str
    category: str
    price: Decimal = Field(ge=0)
    stock_quantity: int = Field(ge=0)
    is_active: bool = True


@router.post("")
def create_product(data: ProductData, db=Depends(get_db), admin=Depends(require_admin)):
    try:
        product_service.create_product(db, data)
        return {"message": "Product created"}
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error))


@router.get("")
def list_products(
    search: Optional[str] = None,
    category: Optional[str] = None,
    is_active: Optional[bool] = None,
    db=Depends(get_db),
):
    return product_service.list_products(db, search, category, is_active)


@router.get("/{product_id}")
def get_product(product_id: int, db=Depends(get_db)):
    product = product_service.get_product(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.put("/{product_id}")
def update_product(
    product_id: int,
    data: ProductData,
    db=Depends(get_db),
    admin=Depends(require_admin),
):
    try:
        if not product_service.update_product(db, product_id, data):
            raise HTTPException(status_code=404, detail="Product not found")
        return {"message": "Product updated"}
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error))


@router.delete("/{product_id}")
def delete_product(
    product_id: int,
    db=Depends(get_db),
    admin=Depends(require_admin),
):
    try:
        if not product_service.delete_product(db, product_id):
            raise HTTPException(status_code=404, detail="Product not found")
        return {"message": "Product deleted"}
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error))
