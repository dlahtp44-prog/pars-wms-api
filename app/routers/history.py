from fastapi import APIRouter, HTTPException
from app.db import get_history, rollback

router = APIRouter(prefix="/api/history", tags=["이력"])

@router.get("")
def history_api(limit: int = 300):
    return get_history(limit=limit)

@router.post("/rollback/{tx_id}")
def rollback_api(tx_id: int):
    ok = rollback(tx_id)
    if not ok:
        raise HTTPException(404, "기록 없음")
    return {"ok": True}
