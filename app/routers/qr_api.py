from fastapi import APIRouter
from app.db import get_inventory

router = APIRouter(prefix="/api", tags=["QR 조회"])

@router.get("/qr-search")
def qr_search(q: str, warehouse: str = "MAIN"):
    # q에 item_code/lot_no/location이 들어와도 검색 가능
    return get_inventory(warehouse=warehouse, location=None, q=q)
