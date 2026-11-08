from fastapi import APIRouter, Depends

from app.database import get_db
from app.services import report_service

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/sales-by-customer")
def sales_by_customer(db=Depends(get_db)):
    return report_service.sales_by_customer(db)


@router.get("/sales-by-product")
def sales_by_product(db=Depends(get_db)):
    return report_service.sales_by_product(db)


@router.get("/monthly-sales")
def monthly_sales(db=Depends(get_db)):
    return report_service.monthly_sales(db)


@router.get("/inventory")
def inventory(db=Depends(get_db)):
    return report_service.inventory(db)
