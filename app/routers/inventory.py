from fastapi import APIRouter
from app.db import get_inventory

router = APIRouter(prefix="/api/inventory", tags=["재고"])

@router.get("")
def api_inventory(q: str = "", warehouse: str = "", location: str = ""):
    w = warehouse or None
    l = location or None
    qq = q or None
    return get_inventory(warehouse=w, location=l, q=qq)
