from fastapi import APIRouter
from app.db import get_inventory

router = APIRouter(prefix="/api", tags=["QR검색"])

@router.get("/qr-search")
def qr_search(q: str = ""):
    # q로 inventory 검색
    return get_inventory(q=q)
