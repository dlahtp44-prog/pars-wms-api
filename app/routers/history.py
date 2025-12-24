from fastapi import APIRouter
from app.db import get_history, rollback

router = APIRouter(prefix="/api/history")

@router.get("")
def history():
    return get_history()

@router.post("/rollback/{hid}")
def history_rollback(hid: int):
    return rollback(hid)
