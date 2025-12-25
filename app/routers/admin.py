from fastapi import APIRouter
from app.db import admin_password_ok

router = APIRouter(prefix="/api/admin", tags=["Admin"])


@router.post("/login")
def admin_login(username: str, password: str):
    ok = admin_password_ok(username, password)
    return {"ok": ok}
