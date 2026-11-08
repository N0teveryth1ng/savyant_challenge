# handles http requests

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.database import get_db
from app.dependencies import get_current_user, require_admin
from app.services import customer_service

router = APIRouter(prefix="/api/customers", tags=["customers"])


class CustomerData(BaseModel):
    name: str
    email: str
    mobile: str
    city: str
    is_active: bool = True


@router.post("", status_code=status.HTTP_201_CREATED)
def create_customer(
    data: CustomerData,
    db=Depends(get_db),
    admin=Depends(require_admin),
):
    try:
        customer_service.create_customer(db, data)
        return {"message": "Customer created"}
    
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error))


@router.get("")
def list_customers(
    search: Optional[str] = None,
    is_active: Optional[bool] = None,
    db=Depends(get_db),
    user=Depends(get_current_user),
):
    return customer_service.list_customers(db, search, is_active, user)


@router.get("/{customer_id}")
def get_customer(customer_id: int, db=Depends(get_db), user=Depends(get_current_user)):
    customer = customer_service.get_customer(db, customer_id, user)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    return customer


@router.put("/{customer_id}")
def update_customer(
    customer_id: int,
    data: CustomerData,
    db=Depends(get_db),
    admin=Depends(require_admin),
):
    try:
        if not customer_service.update_customer(db, customer_id, data):
            raise HTTPException(status_code=404, detail="Customer not found")
        return {"message": "Customer updated"}
    
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error))


@router.delete("/{customer_id}")
def delete_customer(
    customer_id: int,
    db=Depends(get_db),
    admin=Depends(require_admin),
):
    try:
        if not customer_service.delete_customer(db, customer_id):
            raise HTTPException(status_code=404, detail="Customer not found")
        return {"message": "Customer deleted"}
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error))
