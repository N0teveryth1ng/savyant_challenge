import bcrypt
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from app.database import get_db

router = APIRouter()


class LoginData(BaseModel):
    email: str
    password: str


@router.post("/api/login")
def login(data: LoginData, request: Request, db=Depends(get_db)):
    with db.cursor() as cur:
        cur.execute("SELECT * FROM users WHERE email = %s", (data.email,))
        user = cur.fetchone()

    if not user or not bcrypt.checkpw(
        data.password.encode(), user["password_hash"].encode()
    ):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    request.session["user_id"] = user["id"]
    return {"message": "Logged in", "role": user["role"]}


@router.post("/api/logout")
def logout(request: Request):
    request.session.clear()
    return {"message": "Logged out"}
