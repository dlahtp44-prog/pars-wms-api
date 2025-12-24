from fastapi import APIRouter, Query
from app.db import get_inventory

router = APIRouter(prefix="/api/inventory", tags=["재고"])

@router.get("")
def inventory_api(q: str = Query("", description="검색어")):
    return get_inventory(q=q)
