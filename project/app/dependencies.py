from fastapi import Depends, HTTPException, Request
from app.database import get_db


def get_current_user(request: Request, db=Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Login required")

    with db.cursor() as cur:
        cur.execute(
            "SELECT id, name, email, role FROM users WHERE id = %s", (user_id,)
        )
        user = cur.fetchone()

    if not user:
        raise HTTPException(status_code=401, detail="Invalid session")
    return user


def require_admin(user=Depends(get_current_user)):
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user
