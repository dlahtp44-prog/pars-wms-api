# app/routers/history.py
from fastapi import APIRouter
from app.db import get_history

router = APIRouter(prefix="/api/history", tags=["history"])

@router.get("")
def history_api():
    return get_history(500)
