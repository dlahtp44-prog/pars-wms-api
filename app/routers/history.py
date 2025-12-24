from fastapi import APIRouter, HTTPException
from app.db import get_history

router = APIRouter(prefix="/api/history")

@router.get("")
async def read_history(limit: int = 200):
    try:
        data = get_history(limit=limit)
        return data # 리스트 형태로 반환
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
