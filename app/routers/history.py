# app/routers/history.py
from fastapi import APIRouter, HTTPException
from fastapi import Query
from app.db import get_history, rollback

router = APIRouter(prefix="/api/history", tags=["이력"])

@router.get("")
def api_history(limit: int = Query(200), q: str = Query("")):
    return get_history(limit=limit, q=q)

@router.post("/rollback/{tx_id}")
def api_rollback(tx_id: int):
    try:
        rollback(tx_id)
        return {"ok": True}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
