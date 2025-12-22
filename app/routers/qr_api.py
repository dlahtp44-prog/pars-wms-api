from fastapi import APIRouter
from app.db import get_inventory

router = APIRouter(prefix="/api", tags=["QR"])

@router.get("/qr-search")
def qr_search(q: str):
    # 품번/품명/LOT/브랜드로 재고 검색
    return get_inventory(q=q)
