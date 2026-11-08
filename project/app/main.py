from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from pydantic import BaseModel
from fastapi import APIRouter, Depends
from app.database import get_db
import pymysql
from typing import Optional







from app import config
# from app.routers import auth, products, orders   # add as you build them

app = FastAPI(title="Sales Order & Inventory Management")

app.add_middleware(SessionMiddleware, secret_key=config.SECRET_KEY)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# app.include_router(auth.router)
# app.include_router(products.router)
# app.include_router(orders.router)




# initilizing customer data
class CustomerData(BaseModel):
    customer_name: str
    email: str
    phone: Optional[str] = None
    address: Optional[str] = None


# create customer data
@app.post("/customers")
def create_customer_data(user_data: CustomerData, db=Depends(get_db)):
    
    with db.cursor() as cur:
        cur.execute(
            "INSERT INTO customers (customer_name, email, phone, address) "
            "VALUES (%s, %s, %s, %s)",
            (user_data.customer_name, user_data.email, user_data.phone, user_data.address)
        )
    db.commit()
    return {"message": "Customer created"}
    



# get users data (by email)
@app.get("/finduser/{email}")
def retrieve_customers(email: str, db=Depends(get_db)):
    
    with db.cursor() as cur:
        cur.execute("SELECT * FROM customers WHERE EMAIL = %s", (email,))
        customer = cur.fetchone()
    
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer




# delete data
@app.delete("/deleteid/{id}")
def delete_user(id: int, db=Depends(get_db)):
    
    try:
        with db.cursor() as cur:
            cur.execute("DELETE FROM customers WHERE ID = %s ", (id,))
            if cur.rowcount == 0:
                raise HTTPException(status_code=404, detail="Customer not found")
        db.commit()
        return {"message": " customer deleted"}
    
    except pymysql.err.IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Customer has orders and cannot be deleted. Deactivate instead.",
        )
    

        


# filter active/inactive -- (use AI)
@app.get("/customers")
def list_customers(
    search: Optional[str] = None,
    is_active: Optional[bool] = None,
    db=Depends(get_db),
):
    query = "SELECT id, name, email, mobile, city, is_active FROM customers WHERE 1=1"
    params = []

    if search:
        query += " AND (name LIKE %s OR email LIKE %s OR mobile LIKE %s)"
        like = f"%{search}%"
        params += [like, like, like]

    if is_active is not None:
        query += " AND is_active = %s"
        params.append(is_active)

    with db.cursor() as cur:
        cur.execute(query, params)
        return cur.fetchall()































# exception and health checker
@app.get("/health")
def health():
    return {"status": "ok"}


@app.exception_handler(Exception)
def unhandled_error(request: Request, exc: Exception):
    # Never expose tracebacks to the client
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})
