from decimal import Decimal
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.database import get_db
from app.dependencies import get_current_user
from app.services import order_service

router = APIRouter(prefix="/api/orders", tags=["orders"])


class OrderItem(BaseModel):
    product_id: int
    quantity: int = Field(gt=0)


class OrderData(BaseModel):
    customer_id: int
    items: List[OrderItem] = Field(min_length=1)
    discount_percent: Decimal = Field(default=0, ge=0, le=20)


@router.post("", status_code=status.HTTP_201_CREATED)
def create_order(
    data: OrderData,
    db=Depends(get_db),
    user=Depends(get_current_user),
):
    try:
        order_id, order_number = order_service.create_order(db, data, user["id"])
        return {"id": order_id, "order_number": order_number, "status": "draft"}
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))


@router.get("")
def list_orders(db=Depends(get_db), user=Depends(get_current_user)):
    return order_service.list_orders(db, user)


@router.get("/{order_id}")
def get_order(order_id: int, db=Depends(get_db), user=Depends(get_current_user)):
    order = order_service.get_order(db, order_id, user)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@router.put("/{order_id}")
def update_order(
    order_id: int,
    data: OrderData,
    db=Depends(get_db),
    user=Depends(get_current_user),
):
    try:
        if not order_service.update_draft_order(db, order_id, data, user):
            raise HTTPException(status_code=404, detail="Order not found")
        return {"message": "Draft order updated"}
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))


@router.post("/{order_id}/confirm")
def confirm_order(order_id: int, db=Depends(get_db), user=Depends(get_current_user)):
    try:
        changed = order_service.confirm_order(db, order_id, user)
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error))
    if changed is None:
        raise HTTPException(status_code=404, detail="Order not found")
    if not changed:
        return {"message": "Order already processed; no change made"}
    return {"message": "Order confirmed"}


@router.post("/{order_id}/cancel")
def cancel_order(order_id: int, db=Depends(get_db), user=Depends(get_current_user)):
    changed = order_service.cancel_order(db, order_id, user)
    if changed is None:
        raise HTTPException(status_code=404, detail="Order not found")
    if not changed:
        return {"message": "Order already cancelled; no change made"}
    return {"message": "Order cancelled"}
