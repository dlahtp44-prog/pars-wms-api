from fastapi import APIRouter, Query
from app.db import get_inventory, get_location_items

router = APIRouter(prefix="/api/qr", tags=["QR"])

@router.get("/search")
def qr_search(q: str = Query(..., description="검색어(품번/LOT/로케이션 등)")):
    return get_inventory(q=q)

@router.get("/location")
def qr_location(location: str, warehouse: str = "MAIN"):
    return get_location_items(location=location, warehouse=warehouse)
