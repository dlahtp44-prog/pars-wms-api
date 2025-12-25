from fastapi import APIRouter
from app.db import get_history

router = APIRouter(prefix="/api/history", tags=["History"])


@router.get("")
def history_list():
    return get_history()
