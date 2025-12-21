from fastapi import APIRouter
from app.db import get_history

router = APIRouter(prefix="/api", tags=["이력"])

@router.get("/history")
def api_history(limit: int = 200):
    return get_history(limit)
