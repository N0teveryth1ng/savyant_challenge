from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.database import get_db
from app.dependencies import require_admin
from app.services import report_service

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("/customer-sales")
def customer_sales(
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    db=Depends(get_db),
    admin=Depends(require_admin),
):
    return report_service.customer_sales(db, date_from, date_to)


@router.get("/product-sales")
def product_sales(db=Depends(get_db), admin=Depends(require_admin)):
    return report_service.product_sales(db)


@router.get("/low-stock")
def low_stock(
    threshold: int = Query(5, ge=0),
    db=Depends(get_db),
    admin=Depends(require_admin),
):
    return report_service.low_stock(db, threshold)


@router.get("/stock-movements")
def stock_movement_history(db=Depends(get_db), admin=Depends(require_admin)):
    return report_service.stock_movement_history(db)
