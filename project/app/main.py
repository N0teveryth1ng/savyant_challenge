from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app import config
from app.routers import auth, customers, products

app = FastAPI(title="Sales Order & Inventory Management")

app.add_middleware(SessionMiddleware, secret_key=config.SECRET_KEY)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(auth.router)
app.include_router(customers.router)
app.include_router(products.router)




# health check 
@app.get("/health")
def health():
    return {"status": "ok"}


@app.exception_handler(Exception)
def unhandled_error(request: Request, exc: Exception):
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})
