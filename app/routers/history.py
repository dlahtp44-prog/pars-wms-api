# app/routers/history.py
from fastapi import APIRouter, HTTPException
from app.db import get_history, rollback

router = APIRouter(prefix="/api/history", tags=["History"])

@router.get("")
def api_get_history(limit: int = 300):
    return get_history(limit)

@router.post("/rollback/{tx_id}")
def api_rollback(tx_id: int):
    try:
        rollback(tx_id)
        return {"ok": True}
    except Exception as e:
        raise HTTPException(400, str(e))
