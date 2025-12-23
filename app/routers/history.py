from fastapi import APIRouter, HTTPException, Request
from app.db import get_history, rollback
from app.auth import require_admin

router = APIRouter(prefix="/api/history", tags=["이력"])

@router.get("")
def api_history(limit: int = 300):
    return get_history(limit=limit)

@router.post("/rollback/{tx_id}")
def api_rollback(tx_id: int, request: Request):
    require_admin(request)
    try:
        rollback(tx_id)
        return {"ok": True}
    except Exception as e:
        raise HTTPException(400, str(e))
