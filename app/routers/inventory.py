# app/routers/inventory.py
from fastapi import APIRouter, Query
from app.db import get_inventory

router = APIRouter(prefix="/api/inventory", tags=["inventory"])

@router.get("")
def inventory_api(
    warehouse: str = Query(None),
    location: str = Query(None),
    q: str = Query(None),
):
    return get_inventory(warehouse=warehouse, location=location, q=q)
