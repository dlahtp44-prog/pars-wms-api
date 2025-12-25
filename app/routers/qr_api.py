# app/routers/qr_api.py
from fastapi import APIRouter, Query
from app.db import get_location_items, get_inventory

router = APIRouter(prefix="/api", tags=["qr"])

@router.get("/location-items")
def location_items(
    warehouse: str = Query("MAIN"),
    location: str = Query(...)
):
    return get_location_items(warehouse, location)

@router.get("/qr-search")
def qr_search(q: str = Query(...)):
    # 간단 검색: item_code/lot_no/item_name
    return get_inventory(q=q)
