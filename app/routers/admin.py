from fastapi import APIRouter
from app.db import get_admin_logs, rollback_tx

router = APIRouter(prefix="/api/admin", tags=["Admin"])

@router.get("/logs")
def logs():
    return get_admin_logs()

@router.post("/rollback/{tx_id}")
def rollback(tx_id: int):
    rollback_tx(tx_id)
    return {"result": "OK"}
