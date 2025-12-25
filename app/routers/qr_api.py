from fastapi import APIRouter, Query
from app.db import get_location_items

router = APIRouter(prefix="/api/qr", tags=["QR API"])

@router.get("/location")
def location_inventory(
    warehouse: str = Query("MAIN"),
    location: str = Query(...)
):
    items = get_location_items(warehouse, location)
    return {
        "warehouse": warehouse,
        "location": location,
        "items": items
    }
