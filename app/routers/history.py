from fastapi import APIRouter, Depends
from app.db import get_history, rollback
from app.auth import require_admin

router = APIRouter(prefix="/api/history", tags=["history"])

@router.get("")
def api_history(limit: int = 300):
    return get_history(limit=limit)

@router.post("/rollback/{tx_id}")
def api_rollback(tx_id: int, _=Depends(require_admin)):
    rollback(tx_id)
    return {"ok": True}
