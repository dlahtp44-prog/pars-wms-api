from fastapi import APIRouter
from app.db import get_history

router = APIRouter(prefix="/api/history")

@router.get("")
def read_history(limit: int = 200):
    return get_history(limit=limit)
