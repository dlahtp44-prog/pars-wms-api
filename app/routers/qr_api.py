from fastapi import APIRouter, Query
from app.db import get_inventory, get_location_items

router = APIRouter(prefix="/api/qr", tags=["qr-api"])

@router.get("/search")
def qr_search(q: str = Query(...)):
    # item_code/lot/품명 등 검색
    return get_inventory(q=q)

@router.get("/location-items")
def location_items(
    warehouse: str = Query("MAIN"),
    location: str = Query(...)
):
    return get_location_items(warehouse, location)
