from fastapi import APIRouter, Query
from app.db import get_inventory

router = APIRouter(prefix="/api/qr-search", tags=["QR"])

@router.get("")
def qr_search(q: str = Query(...)):
    # q로 재고 검색 (품번/LOT/로케이션 등)
    return get_inventory(q=q)
