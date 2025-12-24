from fastapi import APIRouter, HTTPException
from app.db import get_history

router = APIRouter(prefix="/api/history")

@router.get("")
async def read_history(limit: int = 200):
    try:
        data = get_history(limit=limit)
        # 만약 데이터가 없으면 빈 리스트 [] 를 반환하여 에러를 방지합니다.
        return data if data else []
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
