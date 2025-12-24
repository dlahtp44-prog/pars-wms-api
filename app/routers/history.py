from fastapi import APIRouter
from fastapi.responses import JSONResponse
from app.db import get_history, rollback

router = APIRouter(prefix="/api/history", tags=["이력"])

@router.get("")
def api_history(limit: int = 500):
    return get_history(limit=limit)

@router.post("/rollback/{tx_id}")
def api_rollback(tx_id: int):
    try:
        rollback(tx_id, block_negative=True)
        return {"ok": True}
    except Exception as e:
        return JSONResponse({"ok": False, "detail": str(e)}, status_code=400)
