from fastapi import APIRouter, HTTPException
from app.db import get_history, rollback

router = APIRouter(prefix="/api/history", tags=["이력"])

@router.get("")
def history_api(limit: int = 300):
    return get_history(limit=limit, include_rolled_back=True)

@router.post("/rollback/{tx_id}")
def rollback_api(tx_id: int):
    try:
        return rollback(tx_id)
    except Exception as e:
        raise HTTPException(400, str(e))
