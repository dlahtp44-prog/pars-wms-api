from fastapi import APIRouter, Query
from app.db import get_inventory

router = APIRouter(prefix="/api/inventory", tags=["재고"])

@router.get("")
def api_inventory(
    warehouse: str | None = Query(None),
    location: str | None = Query(None),
    q: str | None = Query(None),
):
    return get_inventory(warehouse=warehouse, location=location, q=q)
