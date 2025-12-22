# routers/qr_process.py
from fastapi import APIRouter
from app.db import log_history

router = APIRouter(prefix="/api/qr", tags=["QR"])

@router.post("/error")
def qr_error(data: dict):
    log_history(
        "QR_ERROR",
        "-", "-", data.get("item_code", "-"),
        "-", 0,
        remark=data.get("reason", "QR 오류")
    )
    return {"result": "오류 기록"}
